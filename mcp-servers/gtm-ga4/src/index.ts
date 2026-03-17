#!/usr/bin/env node

/**
 * GTM + GA4 MCP Server
 *
 * Provides tools to manage Google Tag Manager (tags, triggers, variables)
 * and Google Analytics 4 (custom dimensions) programmatically.
 *
 * Prerequisites:
 *   1. Enable "Tag Manager API" and "Google Analytics Admin API" in GCP Console
 *   2. Create a service account and download the JSON key
 *   3. Grant the service account "Editor" access in GTM container settings
 *   4. Grant the service account "Editor" access in GA4 property settings
 *   5. Set GOOGLE_APPLICATION_CREDENTIALS env var to the key file path
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { google } from "googleapis";

// ── Auth ──

const auth = new google.auth.GoogleAuth({
  scopes: [
    "https://www.googleapis.com/auth/tagmanager.edit.containers",
    "https://www.googleapis.com/auth/tagmanager.publish",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.readonly",
  ],
});

const tagmanager = google.tagmanager({ version: "v2", auth });
const analyticsadmin = google.analyticsadmin({ version: "v1beta", auth });

// ── Server ──

const server = new McpServer({
  name: "gtm-ga4",
  version: "1.0.0",
});

// ── Helpers ──

function ok(data: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }] };
}

function wsParent(accountId: string, containerId: string, workspaceId: string) {
  return `accounts/${accountId}/containers/${containerId}/workspaces/${workspaceId}`;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GTM — Discovery
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

server.tool(
  "gtm_list_accounts",
  "List all GTM accounts accessible by the service account",
  {},
  async () => {
    const { data } = await tagmanager.accounts.list();
    return ok(
      (data.account ?? []).map((a) => ({
        accountId: a.accountId,
        name: a.name,
      })),
    );
  },
);

server.tool(
  "gtm_list_containers",
  "List containers in a GTM account",
  { account_id: z.string().describe("GTM Account ID") },
  async ({ account_id }) => {
    const { data } = await tagmanager.accounts.containers.list({
      parent: `accounts/${account_id}`,
    });
    return ok(
      (data.container ?? []).map((c) => ({
        containerId: c.containerId,
        name: c.name,
        publicId: c.publicId,
      })),
    );
  },
);

server.tool(
  "gtm_list_workspaces",
  "List workspaces in a GTM container",
  {
    account_id: z.string().describe("GTM Account ID"),
    container_id: z.string().describe("GTM Container ID"),
  },
  async ({ account_id, container_id }) => {
    const { data } = await tagmanager.accounts.containers.workspaces.list({
      parent: `accounts/${account_id}/containers/${container_id}`,
    });
    return ok(
      (data.workspace ?? []).map((w) => ({
        workspaceId: w.workspaceId,
        name: w.name,
        description: w.description,
      })),
    );
  },
);

server.tool(
  "gtm_create_workspace",
  "Create a new workspace in a GTM container",
  {
    account_id: z.string().describe("GTM Account ID"),
    container_id: z.string().describe("GTM Container ID"),
    name: z.string().describe("Workspace name"),
    description: z.string().optional().describe("Workspace description"),
  },
  async ({ account_id, container_id, name, description }) => {
    const { data } = await tagmanager.accounts.containers.workspaces.create({
      parent: `accounts/${account_id}/containers/${container_id}`,
      requestBody: { name, description },
    });
    return ok({
      workspaceId: data.workspaceId,
      name: data.name,
    });
  },
);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GTM — Variables
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

server.tool(
  "gtm_list_variables",
  "List all variables in a GTM workspace",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
  },
  async ({ account_id, container_id, workspace_id }) => {
    const { data } =
      await tagmanager.accounts.containers.workspaces.variables.list({
        parent: wsParent(account_id, container_id, workspace_id),
      });
    return ok(
      (data.variable ?? []).map((v) => ({
        variableId: v.variableId,
        name: v.name,
        type: v.type,
      })),
    );
  },
);

server.tool(
  "gtm_create_datalayer_variables",
  "Batch-create Data Layer variables in a GTM workspace",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
    variables: z
      .array(
        z.object({
          variable_name: z.string().describe("Display name, e.g. 'dlv - method'"),
          datalayer_name: z.string().describe("Data Layer key, e.g. 'method'"),
        }),
      )
      .describe("Array of variables to create"),
  },
  async ({ account_id, container_id, workspace_id, variables }) => {
    const parent = wsParent(account_id, container_id, workspace_id);
    const results = await Promise.all(
      variables.map((v) =>
        tagmanager.accounts.containers.workspaces.variables
          .create({
            parent,
            requestBody: {
              name: v.variable_name,
              type: "v",
              parameter: [
                { type: "integer", key: "dataLayerVersion", value: "2" },
                { type: "boolean", key: "setDefaultValue", value: "false" },
                { type: "template", key: "name", value: v.datalayer_name },
              ],
            },
          })
          .then((r) => ({
            name: v.variable_name,
            variableId: r.data.variableId,
            status: "created" as const,
          }))
          .catch((e: Error) => ({
            name: v.variable_name,
            variableId: null,
            status: "error" as const,
            error: e.message,
          })),
      ),
    );
    return ok(results);
  },
);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GTM — Triggers
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

server.tool(
  "gtm_list_triggers",
  "List all triggers in a GTM workspace",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
  },
  async ({ account_id, container_id, workspace_id }) => {
    const { data } =
      await tagmanager.accounts.containers.workspaces.triggers.list({
        parent: wsParent(account_id, container_id, workspace_id),
      });
    return ok(
      (data.trigger ?? []).map((t) => ({
        triggerId: t.triggerId,
        name: t.name,
        type: t.type,
      })),
    );
  },
);

server.tool(
  "gtm_create_custom_event_trigger",
  "Create a Custom Event trigger in a GTM workspace",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
    trigger_name: z.string().describe("Trigger display name"),
    event_name: z.string().describe("Event name or regex pattern"),
    use_regex: z
      .boolean()
      .default(false)
      .describe("Use regex matching for event name"),
    exclude_pattern: z
      .string()
      .optional()
      .describe("Exclude events containing this string"),
  },
  async ({
    account_id,
    container_id,
    workspace_id,
    trigger_name,
    event_name,
    use_regex,
    exclude_pattern,
  }) => {
    const parent = wsParent(account_id, container_id, workspace_id);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const requestBody: any = {
      name: trigger_name,
      type: "customEvent",
      customEventFilter: [
        {
          type: use_regex ? "matchRegex" : "equals",
          parameter: [
            { type: "template", key: "arg0", value: "{{_event}}" },
            { type: "template", key: "arg1", value: event_name },
          ],
        },
      ],
    };

    if (exclude_pattern) {
      requestBody.filter = [
        {
          type: "contains",
          negate: true,
          parameter: [
            { type: "template", key: "arg0", value: "{{_event}}" },
            { type: "template", key: "arg1", value: exclude_pattern },
          ],
        },
      ];
    }

    const { data } =
      await tagmanager.accounts.containers.workspaces.triggers.create({
        parent,
        requestBody,
      });

    return ok({ triggerId: data.triggerId, name: data.name });
  },
);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GTM — Tags
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

server.tool(
  "gtm_list_tags",
  "List all tags in a GTM workspace",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
  },
  async ({ account_id, container_id, workspace_id }) => {
    const { data } =
      await tagmanager.accounts.containers.workspaces.tags.list({
        parent: wsParent(account_id, container_id, workspace_id),
      });
    return ok(
      (data.tag ?? []).map((t) => ({
        tagId: t.tagId,
        name: t.name,
        type: t.type,
        firingTriggerId: t.firingTriggerId,
      })),
    );
  },
);

server.tool(
  "gtm_create_google_tag",
  "Create a Google Tag (GA4 config) in GTM — fires on page load to initialize GA4",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
    tag_name: z.string().describe("Tag display name"),
    tag_id: z.string().describe("Measurement ID, e.g. G-XXXXXXXX"),
    trigger_id: z.string().describe("Trigger ID (use All Pages trigger)"),
  },
  async ({ account_id, container_id, workspace_id, tag_name, tag_id, trigger_id }) => {
    const { data } =
      await tagmanager.accounts.containers.workspaces.tags.create({
        parent: wsParent(account_id, container_id, workspace_id),
        requestBody: {
          name: tag_name,
          type: "googtag",
          parameter: [
            { type: "template", key: "tagId", value: tag_id },
          ],
          firingTriggerId: [trigger_id],
        },
      });
    return ok({ tagId: data.tagId, name: data.name });
  },
);

server.tool(
  "gtm_create_ga4_event_tag",
  "Create a GA4 Event tag in GTM — forwards dataLayer events to GA4",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
    tag_name: z.string().describe("Tag display name"),
    measurement_id: z.string().describe("GA4 Measurement ID, e.g. G-XXXXXXXX"),
    event_name: z
      .string()
      .describe("Event name or GTM variable, e.g. '{{Event}}' for dynamic"),
    event_parameters: z
      .array(
        z.object({
          name: z.string().describe("Parameter name"),
          value: z.string().describe("Parameter value or variable, e.g. '{{dlv - method}}'"),
        }),
      )
      .optional()
      .describe("Event parameters to forward to GA4"),
    trigger_id: z.string().describe("Trigger ID to fire this tag"),
  },
  async ({
    account_id,
    container_id,
    workspace_id,
    tag_name,
    measurement_id,
    event_name,
    event_parameters,
    trigger_id,
  }) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const params: any[] = [
      { type: "template", key: "eventName", value: event_name },
      { type: "template", key: "measurementIdOverride", value: measurement_id },
    ];

    if (event_parameters && event_parameters.length > 0) {
      params.push({
        type: "list",
        key: "eventParameters",
        list: event_parameters.map((p) => ({
          type: "map",
          map: [
            { type: "template", key: "name", value: p.name },
            { type: "template", key: "value", value: p.value },
          ],
        })),
      });
    }

    const { data } =
      await tagmanager.accounts.containers.workspaces.tags.create({
        parent: wsParent(account_id, container_id, workspace_id),
        requestBody: {
          name: tag_name,
          type: "gaawe",
          parameter: params,
          firingTriggerId: [trigger_id],
        },
      });

    return ok({ tagId: data.tagId, name: data.name });
  },
);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GTM — Publish
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

server.tool(
  "gtm_publish",
  "Create a version from the workspace and publish it to live",
  {
    account_id: z.string(),
    container_id: z.string(),
    workspace_id: z.string(),
    version_name: z.string().describe("Version name for this publish"),
  },
  async ({ account_id, container_id, workspace_id, version_name }) => {
    // Step 1: Create a version from the workspace
    const { data: versionData } =
      await tagmanager.accounts.containers.workspaces.create_version({
        path: wsParent(account_id, container_id, workspace_id),
        requestBody: { name: version_name },
      });

    if (versionData.compilerError) {
      return ok({
        status: "error",
        compilerError: versionData.compilerError,
      });
    }

    const versionId = versionData.containerVersion?.containerVersionId;
    if (!versionId) {
      return ok({ status: "error", message: "Failed to create version" });
    }

    // Step 2: Publish the version
    const { data: publishData } =
      await tagmanager.accounts.containers.versions.publish({
        path: `accounts/${account_id}/containers/${container_id}/versions/${versionId}`,
      });

    return ok({
      status: "published",
      versionId: publishData.containerVersion?.containerVersionId,
      name: version_name,
    });
  },
);

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  GA4 — Properties & Custom Dimensions
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

server.tool(
  "ga4_list_properties",
  "List all GA4 properties accessible by the service account",
  {},
  async () => {
    const { data } = await analyticsadmin.accountSummaries.list();
    const properties: { propertyId: string; displayName: string; account: string }[] = [];
    for (const account of data.accountSummaries ?? []) {
      for (const prop of account.propertySummaries ?? []) {
        properties.push({
          propertyId: prop.property?.replace("properties/", "") ?? "",
          displayName: prop.displayName ?? "",
          account: account.displayName ?? "",
        });
      }
    }
    return ok(properties);
  },
);

server.tool(
  "ga4_list_custom_dimensions",
  "List custom dimensions for a GA4 property",
  {
    property_id: z.string().describe("GA4 Property ID (numeric)"),
  },
  async ({ property_id }) => {
    const { data } = await analyticsadmin.properties.customDimensions.list({
      parent: `properties/${property_id}`,
    });
    return ok(
      (data.customDimensions ?? []).map((d) => ({
        displayName: d.displayName,
        parameterName: d.parameterName,
        scope: d.scope,
      })),
    );
  },
);

server.tool(
  "ga4_create_custom_dimensions",
  "Batch-create custom dimensions for a GA4 property",
  {
    property_id: z.string().describe("GA4 Property ID (numeric)"),
    dimensions: z
      .array(
        z.object({
          display_name: z.string().describe("Display name in GA4 reports"),
          parameter_name: z.string().describe("Event parameter name"),
          scope: z.enum(["EVENT", "USER"]).default("EVENT"),
        }),
      )
      .describe("Array of custom dimensions to create"),
  },
  async ({ property_id, dimensions }) => {
    const results = await Promise.all(
      dimensions.map((d) =>
        analyticsadmin.properties.customDimensions
          .create({
            parent: `properties/${property_id}`,
            requestBody: {
              displayName: d.display_name,
              parameterName: d.parameter_name,
              scope: d.scope,
            },
          })
          .then(() => ({
            displayName: d.display_name,
            parameterName: d.parameter_name,
            status: "created" as const,
          }))
          .catch((e: Error) => ({
            displayName: d.display_name,
            parameterName: d.parameter_name,
            status: "error" as const,
            error: e.message,
          })),
      ),
    );
    return ok(results);
  },
);

// ── Start ──

const transport = new StdioServerTransport();
await server.connect(transport);
