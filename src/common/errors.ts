/** Invalid builder input. The message says what to change; tools pass it to the model as is. */
export class UrlBuilderError extends Error {
  override name = "UrlBuilderError";
}
