<template>
  <v-combobox
    :items="hints"
    @keydown.enter="onSearch"
    @click:clear="$emit('clear')"
    @click="menu = true"
    v-model="valueInternal"
    v-model:menu="menu"
    ref="searchInput"
    item-props
    item-title="key"
    item-value="key"
    density="compact"
    clearable
    :loading="isFetchingHints"
    hide-no-data
    variant="solo"
    v-bind="inputAttrs"
    no-filter
    hide-details
  >
    <template #item="{ props, item }">
      <v-list-item
        v-bind="props"
        density="compact"
        @pointerdown="onHintSelected($event, item.raw)"
        @keydown.enter="onHintSelected($event, item.raw)"
        @keydown.right="onHintRight($event, item.raw)"
      >
        <template #prepend>
          <v-icon size="x-small">{{
            item.raw.type === EnumHistoryTypes.DATABASE
              ? "mdi-magnify"
              : "mdi-history"
          }}</v-icon>
        </template>
        <template #title>
          <v-list-item-title
            :class="{
              'text-accent': item.raw.type !== EnumHistoryTypes.DATABASE,
            }"
            class="font-weight-regular"
            v-html="boldStart(item.raw.key, valueInternal)"
          ></v-list-item-title>
        </template>
        <template #append>
          <v-list-item-action
            tabindex="-1"
            class="ma-0 pa-0"
            v-if="item.raw.type !== EnumHistoryTypes.DATABASE"
          >
            <v-btn
              tabindex="-1"
              icon
              variant="text"
              size="x-small"
              @click.stop="deleteHint(item.raw)"
            >
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </v-list-item-action>
        </template>
      </v-list-item>
    </template>

    <template v-if="appendSearchButton" #append>
      <v-list-item-action>
        <v-btn color="primary" @click="onSearch">Search</v-btn>
      </v-list-item-action>
    </template>
  </v-combobox>
</template>

<script lang="ts">
import {
  Component,
  Vue,
  Prop,
  Ref,
  Watch,
  toNative,
} from "vue-facing-decorator";
import { fromEvent, from } from "rxjs";
import { debounceTime, map, switchMap, tap } from "rxjs/operators";
import SearchHistory from "@/models/search-history.model";
import Search from "@/models/search.model";
import type { VTextField } from "vuetify/lib/components/index.mjs";
import { EnumHistoryTypes, IHint } from "@/types";

const typeaheadDebounceTime = 500;

@Component({
  name: "cd-search",
  components: {},
  emits: ["update:model-value", "hint-selected", "clear"],
})
class CdSearch extends Vue {
  @Prop() modelValue!: string;
  @Prop({ default: true }) appendSearchButton!: boolean;
  @Prop({ default: false }) autoFocus!: boolean;
  /** If `true`, the component will emit  the `update:model-value` event on every keystroke without debounce */
  @Prop({ default: false }) isEager!: boolean;
  @Prop({ default: () => ({}) }) inputAttrs: any;
  @Prop({ default: EnumHistoryTypes.TERM }) targetField!: EnumHistoryTypes;
  @Ref("searchInput") searchInput!: InstanceType<typeof VTextField>;

  valueInternal = "";
  previousValueInternal = "";
  hints: IHint[] = []; // used to reactively bind to template
  menu = false;
  isFetchingHints = false;
  rawDbHints: any[] = [];
  EnumHistoryTypes = EnumHistoryTypes;

  public get typeaheadHints(): IHint[] {
    if (!this.rawDbHints || !this.valueInternal) {
      return this.localHints;
    }

    return [...this.localHints, ...this.dbHints];
  }

  public get localHints(): IHint[] {
    return SearchHistory.searchHints(
      this.valueInternal || "",
      this.targetField,
    );
  }

  public get dbHints(): IHint[] {
    const minCharacters = 3;
    const valueInternal = this.valueInternal.toLocaleLowerCase();

    let hints = this.rawDbHints
      .map((h) => h.highlights)
      .flat()
      .map((h) => h.texts)
      .flat()
      .filter(
        (t) =>
          t.type === "hit" &&
          t.value.length > minCharacters &&
          t.value.toLowerCase().indexOf(valueInternal) >= 0,
      )
      .map((t) => t.value.toLowerCase())
      .filter(
        (v: string) =>
          v !== valueInternal && !this.localHints.some((h) => h.key === v),
      );
    hints = [...new Set(hints)].slice(0, 10) as string[]; // get unique ones
    hints = hints.map((key) => ({ type: "db", key }) as IHint);
    return hints;
  }

  @Watch("valueInternal")
  onValueInternalChanged() {
    if (!this.valueInternal) {
      this.hints = this.localHints;
    }
  }

  created() {
    // @ts-ignore Vuetify component needs `null` instead of empty string initially
    this.valueInternal = this.modelValue || null;
  }

  async mounted() {
    this.previousValueInternal = this.modelValue;
    try {
      await this._onTypeahead();
    } catch (e) {}
    this.hints = this.typeaheadHints;

    // Initially, set focus on the input, but hide menu.
    if (this.autoFocus) {
      setTimeout(() => {
        this.searchInput?.focus();
        this.menu = false;
      }, 0);
    }

    // https://www.learnrxjs.io/learn-rxjs/recipes/type-ahead
    if (this.searchInput) {
      fromEvent(this.searchInput?.$el, "input")
        .pipe(
          tap(() => {
            this.isFetchingHints = !!this.valueInternal;
            // Show hints from local history while the database ones load
            this.hints = this.localHints;
            this.menu = true;
            if (this.isEager) {
              this.$emit("update:model-value", this.valueInternal);
            }
          }),
          debounceTime(typeaheadDebounceTime),
          map((e: any) => e.target.value),
          switchMap(() => from(this._onTypeahead())),
        )
        .subscribe(() => {
          this._handleTypeahead();
        });
    }
  }

  public onSearch() {
    this.previousValueInternal = this.valueInternal;
    this.menu = false;
    this.$emit("update:model-value", this.valueInternal);
  }

  public async onHintSelected(event: PointerEvent, hint: IHint) {
    // Ignore clicks on the action buttons
    if (
      // @ts-ignore
      event.target?.classList.contains("mdi-close")
    ) {
      return;
    }

    this.valueInternal = hint.key;
    this.isFetchingHints = !!this.valueInternal;
    this.onSearch();
    this.$emit("hint-selected", this.valueInternal);
  }

  public async onHintRight(_event: PointerEvent, hint: IHint) {
    this.valueInternal = hint.key;
    this.searchInput?.focus();
  }

  public deleteHint(hint: IHint) {
    SearchHistory.deleteHint(hint.key);
    this.hints = this.typeaheadHints;
  }

  async _onTypeahead() {
    if (!this.valueInternal?.trim?.()) {
      this.isFetchingHints = false;
      this.hints = this.typeaheadHints;
      return;
    }

    try {
      this.previousValueInternal = this.valueInternal;
      this.rawDbHints = await Search.typeahead({
        term: this.valueInternal,
        field: this.targetField,
      });
      this.isFetchingHints = false;
    } catch (e) {
      console.log(e);
    }
  }

  public boldStart(title: string, startStr: string) {
    if (title.indexOf(startStr) >= 0) {
      return title.replace(startStr, `<b>${startStr}</b>`);
    }
    return title;
  }

  _handleTypeahead() {
    this.hints = this.typeaheadHints;
    if (this.valueInternal) {
      this.isFetchingHints = false;
    }
  }
}
export default toNative(CdSearch);
</script>

<style lang="scss" scoped>
.cd-home-search {
  background: #ddd;
}

.search-container {
  max-width: 45rem;
}
</style>
