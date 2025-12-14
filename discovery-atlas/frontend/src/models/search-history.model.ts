import { EnumHistoryTypes, IHint } from "@/types";
import { Model } from "@vuex-orm/core";

export interface ISearchHistoryState { }

export interface ISearch {
  key: string;
  date: number;
  type: string;
}

export default class SearchHistory extends Model implements ISearch {
  static entity = "search-history";
  static primaryKey = "key";
  public readonly key!: string;
  public readonly date!: number;
  public readonly type!: string;

  static fields() {
    return {
      key: this.attr(""),
      type: this.attr(""),
      date: this.attr(0),
    };
  }

  static beforeSelect(documents: SearchHistory[]) {
    const validTypes = Object.values(EnumHistoryTypes)
    // Preprocess existing documents created before implementation of multiple history types
    documents.forEach((doc) => {
      if (!validTypes.includes(doc.type as EnumHistoryTypes)) {
        doc.$update({ type: EnumHistoryTypes.TERM })
      }
    })
    return documents
  }

  static get $state(): ISearchHistoryState {
    return this.store().state.entities[this.entity];
  }

  static state(): ISearchHistoryState {
    return {};
  }

  public static log(key: string, type: EnumHistoryTypes) {
    SearchHistory.insert({ data: { key, type, date: Date.now() } });
  }

  public static searchHints(searchString: string, type: EnumHistoryTypes) {
    const str = searchString.trim().toLowerCase();

    const allHints = this.all()
      .sort((a, b) => b.date - a.date)
      .filter(hint => hint.type === type)
      .map(hint => ({ type: hint.type, key: hint.key })) as IHint[]

    if (!str) {
      return allHints.slice(0, 10);
    }
    else {
      return allHints.filter((entry) => {
        const val = entry.key.toLowerCase();
        return val.includes(str) && val.length > str.length;
      })
    }
  }

  public static deleteHint(key: string) {
    this.delete(key);
  }
}
