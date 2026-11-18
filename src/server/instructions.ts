/**
 * Server instructions sent to the client at initialization. The full text (inform rather
 * than conclude, standard data first, KML only for GIS users, the MAP_KEY reminder) is
 * written with the tools in WK-23; it points to FAQ entries by ID and never paraphrases them
 * (ADR-0011 §5).
 */
export const INSTRUCTIONS = [
  "This server gives you NASA FIRMS's own documentation, verbatim, and builds FIRMS Fire Map",
  "and FIRMS API URLs. It does not answer science questions: present FIRMS's data paths,",
  "wording, and caveats so the user can reach their own conclusion.",
  "It is not an official NASA product.",
].join(" ");
