/** Stringify a JSON object and avoid circular references */
export function stringify(obj: any) {
  let cache: any = [];
  const str = JSON.stringify(obj, function (_key, value) {
    if (typeof value === "object" && value !== null) {
      if (cache.indexOf(value) !== -1) {
        // Circular reference found, discard key
        return;
      }
      cache.push(value);
    }
    return value;
  });
  cache = null;
  return str;
}
