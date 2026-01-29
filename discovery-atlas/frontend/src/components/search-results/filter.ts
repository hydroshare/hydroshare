import { INITIAL_RANGE, MAX_YEAR, MIN_YEAR } from "@/constants";
import { EnumHistoryTypes, EnumShortParams } from "@/types";
import { LocationQuery } from "vue-router";

export enum EnumFilterTypes {
  RANGE = 'Range',
  SELECT_MULTIPLE = 'Select Multiple',
  SELECT_ONE = 'Select One',
  NUMBER = 'Number',
  STRING = 'String'
}

export interface IFilterOption { value: any, label: string, hint?: string, icon?: string, logo?: string }

export class Filter {
  /** Required if type is `EnumFilterTypes.RANGE`. Defaults to `MIN_YEAR` */
  min?: number
  /** Required if type is `EnumFilterTypes.RANGE`. Defaults to `MAX_YEAR` */
  max?: number
  /** Required if type is `EnumFilterTypes.SELECT_MULTIPLE` */
  options?: IFilterOption[]
  type: string = 'default'
  name: string;
  title: string;
  icon?: string;
  urlLabel: EnumShortParams;
  historyType?: EnumHistoryTypes;
  private _value: any = null;
  private _isEnabled: boolean = false;
  private _getter?: () => any
  private _setter?: (val: any) => void;
  private _clear?: () => void;

  constructor(params: { name: string, title: string, urlLabel: EnumShortParams, icon?: string, type: EnumFilterTypes, min?: number, max?: number, options?: IFilterOption[], historyType?: EnumHistoryTypes, getter?: () => any, setter?: (val: any) => void, clear?: () => void }) {
    this.name = params.name;
    this.title = params.title;
    this.urlLabel = params.urlLabel;
    this.type = params.type

    if (this.type == EnumFilterTypes.RANGE) {
      this.min = params.hasOwnProperty('min') ? params.min : MIN_YEAR
      this.max = params.hasOwnProperty('max') ? params.max : MAX_YEAR
    }
    else if (this.type === EnumFilterTypes.SELECT_MULTIPLE || this.type === EnumFilterTypes.SELECT_ONE) {
      this.options = params.options
    }

    if (params.getter) {
      this._getter = params.getter
    }
    if (params.setter) {
      this._setter = params.setter
    }
    if (params.clear) {
      this._clear = params.clear
    }
    if (params.historyType) {
      this.historyType = params.historyType
    }
    if (params.icon) {
      this.icon = params.icon
    }
  }

  get value() {
    return this._getter ? this._getter() : this._value;
  }

  set value(val: any) {
    this._setter ? this._setter(val) : this._value = val;
  }

  get isEnabled() {
    return this._isEnabled
  }

  set isEnabled(val: boolean) {
    this._isEnabled = val;
  }

  isActive(): boolean {
    if (this.type === EnumFilterTypes.RANGE) {
      return this.isEnabled
    }
    if (this.type === EnumFilterTypes.SELECT_MULTIPLE) {
      return this.isEnabled && this.value?.length
    }
    else {
      return !!this.value
    }
  }

  enable() {
    this.isEnabled = true;
  }

  disable() {
    this.isEnabled = false;
  }

  toggle() {
    this.isEnabled = !this.isEnabled;
  }

  clear() {
    this._clear ? this._clear() : (this.value = this.type === EnumFilterTypes.RANGE ? INITIAL_RANGE : null);
    this.disable();
  }

  getQueryParams() {
    if (!this.isEnabled || !this.value) {
      return {}
    }
    if (this.type === EnumFilterTypes.RANGE) {
      return {
        [`${this.name}Start`]: this.value[0],
        [`${this.name}End`]: this.value[1],
      }
    }
    else {
      return { [this.name]: this.value }
    }
  }

  getRouteParams() {
    if (this.type === EnumFilterTypes.RANGE) {
      return {
        [this.urlLabel]: this.isEnabled ? this.value.map((n: number) => n.toString() || undefined) : undefined
      }
    }
    else if (this.type === EnumFilterTypes.SELECT_MULTIPLE) {
      return {
        [this.urlLabel]: this.isEnabled ? this.value || undefined : undefined
      }
    }
    else {
      return { [this.urlLabel]: this.value || undefined }
    }
  }

  loadFromRoute(query: LocationQuery) {
    if (query[this.urlLabel]) {
      this.isEnabled = true;

      if (this.type === EnumFilterTypes.RANGE)
        this.value =
          ((
            query[this.urlLabel] as [
              string,
              string,
            ]
          )?.map((n) => +n) as [number, number]) || this.value;
      else if (this.type === EnumFilterTypes.SELECT_MULTIPLE) {
        if (query[this.urlLabel]) {
          this.isEnabled = true;
          this.value = query[
            this.urlLabel
          ]
            ? ([query[this.urlLabel]].flat() as string[])
            : null;
        }
      }
      else {
        this.value = (query[this.urlLabel] as string) || "";
      }
    }
  }
}