export { fold, markdownToPlain, missingLines } from "./completeness.js";
export { FrontMatterError, join, split } from "./frontmatter.js";
export {
  configuredKnowledgeDirs,
  defaultKnowledgeDir,
  KNOWLEDGE_DIRS_ENV,
  KnowledgeBase,
  KnowledgeBaseError,
  loadKnowledgeBase,
  type SearchOptions,
  type Section,
} from "./loader.js";
export { contentHash, type KnowledgeEntry, type KnowledgeSource } from "./models.js";
export { makeSnippet, type SearchHit, tokenize } from "./search.js";
