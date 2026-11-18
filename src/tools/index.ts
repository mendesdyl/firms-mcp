/**
 * Every tool the server registers, in the order `tools/list` returns them (FR-MCP-008): the
 * seven `firms_` tools of ADR-0011 §3, knowledge first, then URL building, then the catalog.
 */
import type { DefinedTool } from "./definition.js";
import { buildApiUrl } from "./firms_build_api_url/tool.js";
import { buildFireMapUrl } from "./firms_build_fire_map_url/tool.js";
import { buildKmlFootprintTool } from "./firms_build_kml_footprint_url/tool.js";
import { getKnowledgeEntry } from "./firms_get_knowledge_entry/tool.js";
import { listDataSources } from "./firms_list_data_sources/tool.js";
import { listKnowledgeTopics } from "./firms_list_knowledge_topics/tool.js";
import { searchKnowledge } from "./firms_search_knowledge/tool.js";

export const TOOLS: readonly DefinedTool[] = [
  searchKnowledge,
  getKnowledgeEntry,
  listKnowledgeTopics,
  buildFireMapUrl,
  buildApiUrl,
  buildKmlFootprintTool,
  listDataSources,
];
