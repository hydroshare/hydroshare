import { ISearchParams, ITypeaheadParams } from "./types";

/** Transforms the values in a dictionary into strings, and filters out falsey entries and array entries
 * Array values need to be stringified with `stringifyArrayParamValues`
 * @returns the resulting object after filter and transformation
 */
function _stringifyPrimitiveParamValues(
  params: ISearchParams | ITypeaheadParams | { [key: string]: string }
): { [key: string]: string } {
  return Object.fromEntries(
    Object.entries(params)
      .filter(([key, value]) => !Array.isArray(value) && !!value)
      .map(([key, value]) => {
        return [key, String(value)];
      })
  );
}

/** Filters array items from a param object and returns a concatenation of query strings
 * i.e: `{ foo: ['bar', 'baz'] }` => `'&foo=bar&foo=baz'`
 * @returns a concatenation of array query strings
 */
function _stringifyArrayParamValues(
  params: ISearchParams | ITypeaheadParams | { [key: string]: string }
): string {
  return Object.entries(params)
    .filter(([key, value]) => Array.isArray(value) && value.length > 0)
    .map(([key, value]) => {
      return value.map((v) => `&${key}=${encodeURIComponent(v)}`).join("");
    })
    .join("");
}

export function getQueryString(
  params: ISearchParams | ITypeaheadParams | { [key: string]: string }
): string {
  const primitiveParams = _stringifyPrimitiveParamValues(params);
  const arrayParams = _stringifyArrayParamValues(params);
  return `${new URLSearchParams(primitiveParams)}${arrayParams}`;
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("en-us", {
    year: "numeric",
    month: "numeric",
    day: "2-digit",
    // hour: "2-digit",
    // minute: "2-digit",
    // hour12: false,
  });
}
