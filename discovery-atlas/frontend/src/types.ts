import type { ViteSSGContext } from "vite-ssg";

export type UserModule = (ctx: ViteSSGContext) => void;

export interface IResult {
  id: string;
  creator: string[];
  dateCreated: string;
  datePublished: string;
  lastModified: string;
  description: string;
  highlights: {
    path: string;
    score: number;
    texts: {
      type: string;
      value: string;
    }[];
  }[];
  license: string;
  keywords: string[];
  name: string;
  score: number; // unused for now...
  url: string;
  identifier: string;
  funding: string[];
  spatialCoverage: any;
  contentType: string;
  sharingStatus: string;
  _showMore?: boolean; // Used to toggle 'show more...' button
  _paginationToken: string;
}

export interface IHint {
  type: EnumHistoryTypes;
  key: string;
}

export interface ISearchParams {
  term: string;
  sortBy?: string;
  order?: "asc" | "desc";
  pageSize: number;
  pageNumber: number;
  publishedStart?: number;
  publishedEnd?: number;
  dateCreatedStart?: number;
  dateCreatedEnd?: number;
  dataCoverageStart?: number;
  dataCoverageEnd?: number;
  creatorName?: string;
  // ownerName?: string;
  fundingFunderName?: string;
  keyword?: string;
  creativeWorkStatus?: string[];
  contentType?: string[];
  paginationToken?: string;
}

export interface ITypeaheadParams {
  term: string;
  field: EnumHistoryTypes;
}

export enum EnumShortParams {
  QUERY = "q",
  AUTHOR_NAME = "an",
  OWNER_NAME = "on",
  CONTENT_TYPE = "ct",
  FUNDER = "f",
  SUBJECT = "sj",
  AVAILABILITY = "a",
  CREATION_DATE = "cd",
  PUBLICATION_YEAR = "py",
  DATA_COVERAGE = "dc",
}

export enum EnumHistoryTypes {
  TERM = "term",
  CREATOR = "creator",
  SUBJECT = "subject",
  FUNDER = "funder",
  DATABASE = "db",
}

export type EnumDictionary<T extends string | symbol | number, U> = {
  [K in T]: U;
};

const a = [
  {
    $search: {
      index: "fuzzy_search",
      compound: {
        filter: [{ term: { path: "type", query: "Dataset" } }],
        must: [],
        should: [
          {
            autocomplete: {
              query: "water",
              path: "name",
              fuzzy: { maxEdits: 1 },
              score: { boost: { value: 5 } },
            },
          },
          {
            autocomplete: {
              query: "water",
              path: "description",
              fuzzy: { maxEdits: 1 },
              score: { boost: { value: 3 } },
            },
          },
          {
            autocomplete: {
              query: "water",
              path: "keywords",
              fuzzy: { maxEdits: 1 },
              score: { boost: { value: 3 } },
            },
          },
          {
            autocomplete: {
              query: "water",
              path: "creator.name",
              fuzzy: { maxEdits: 1 },
              score: { boost: { value: 5 } },
            },
          },
        ],
      },
      highlight: { path: ["name", "description", "keywords", "creator.name"] },
      concurrent: true,
      returnStoredSource: true,
      sort: { $meta: "searchScore" },
    },
  },
  {
    $set: {
      score: { $meta: "searchScore" },
      highlights: { $meta: "searchHighlights" },
      paginationToken: { $meta: "searchSequenceToken" },
    },
  },
  { $match: { dateCreated: { $not: { $eq: null } } } },
  { $match: { score: { $gt: 10.0 } } },
  { $limit: 20 },
  {
    $lookup: {
      from: "discovery",
      localField: "_id",
      foreignField: "_id",
      as: "document",
    },
  },
];
