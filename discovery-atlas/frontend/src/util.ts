import { ISearchParams, ITypeaheadParams } from "./types";

// https://wiki.ubuntu.com/UnitsPolicy
const kib = 1024;
const mib = 1024 * kib;
const gib = 1024 * mib;
const tib = 1024 * gib;

const kb = 1000;
const mb = 1024 * kb;
const gb = 1024 * mb;
const tb = 1024 * gb;

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

/**
 * @param size The size containing the amount and unit separated by a space. i.e.: 21 MB
 * @returns The size in bytes
 */
export function sizeToBytes(size: string, separator = " "): number {
  let fileSizeBytes;

  if (typeof size === "string") {
    const parts = size.trim().split(separator);
    if (parts.length == 2) {
      const num = +parts[0];
      const notation = parts[1].toLowerCase();

      let multiplier = 0;

      switch (notation) {
        case "b":
          multiplier = 1;
          break;
        case "kb":
          multiplier = kb;
          break;
        case "mb":
          multiplier = mb;
          break;
        case "gb":
          multiplier = gb;
          break;
        case "tb":
          multiplier = tb;
          break;
        case "kib":
          multiplier = kib;
          break;
        case "mib":
          multiplier = mib;
          break;
        case "gib":
          multiplier = gib;
          break;
        case "tib":
          multiplier = tib;
          break;
      }
      fileSizeBytes = num * multiplier;
    }
  }

  return fileSizeBytes || 0;
}
