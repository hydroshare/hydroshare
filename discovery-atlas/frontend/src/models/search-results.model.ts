import { Model } from "@vuex-orm/core";
import { INITIAL_RANGE } from "@/constants";

export interface ISearchResultsState {
  publicationYear: [number, number];
  dataCoverage: [number, number];
  creationDate: [number, number];
  panels: number[];
}

export default class SearchResults extends Model {
  static entity = "search-results";

  static fields() {
    return {};
  }

  static get $state(): ISearchResultsState {
    return this.store().state.entities[this.entity];
  }

  static state(): ISearchResultsState {
    return {
      publicationYear: INITIAL_RANGE,
      dataCoverage: INITIAL_RANGE,
      creationDate: INITIAL_RANGE,
      panels: [],
    };
  }
}
