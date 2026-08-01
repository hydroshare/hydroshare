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

<script setup lang="ts">
import { fromEvent, from } from "rxjs";
import { debounceTime, map, switchMap, tap } from "rxjs/operators";
import SearchHistory from "@/models/search-history.model";
import Search from "@/models/search.model";
import type { VTextField } from "vuetify/lib/components/index.mjs";
import { EnumHistoryTypes, IHint } from "@/types";

const typeaheadDebounceTime = 500;

const props = withDefaults(
  defineProps<{
    modelValue: string;
    appendSearchButton?: boolean;
    autoFocus?: boolean;
    /** If `true`, the component will emit the `update:model-value` event on every keystroke without debounce */
    isEager?: boolean;
    inputAttrs?: any;
    targetField?: EnumHistoryTypes;
  }>(),
  {
    appendSearchButton: true,
    autoFocus: false,
    isEager: false,
    inputAttrs: () => ({}),
    targetField: EnumHistoryTypes.TERM,
  },
);

const emit = defineEmits(["update:model-value", "hint-selected", "clear"]);

const searchInput = useTemplateRef<InstanceType<typeof VTextField>>("searchInput");

const valueInternal = ref<string>("");
const previousValueInternal = ref("");
const hints = ref<IHint[]>([]); // used to reactively bind to template
const menu = ref(false);
const isFetchingHints = ref(false);
const rawDbHints = ref<any[]>([]);

const localHints = computed<IHint[]>(() =>
  SearchHistory.searchHints(valueInternal.value || "", props.targetField),
);

const dbHints = computed<IHint[]>(() => {
  const minCharacters = 3;
  const value = valueInternal.value.toLocaleLowerCase();

  let list = rawDbHints.value
    .map((h) => h.highlights)
    .flat()
    .map((h) => h.texts)
    .flat()
    .filter(
      (t) =>
        t.type === "hit" &&
        t.value.length > minCharacters &&
        t.value.toLowerCase().indexOf(value) >= 0,
    )
    .map((t) => t.value.toLowerCase())
    .filter(
      (v: string) => v !== value && !localHints.value.some((h) => h.key === v),
    );
  list = [...new Set(list)].slice(0, 10) as string[]; // get unique ones
  return list.map((key) => ({ type: "db", key }) as IHint);
});

const typeaheadHints = computed<IHint[]>(() => {
  if (!rawDbHints.value || !valueInternal.value) {
    return localHints.value;
  }
  return [...localHints.value, ...dbHints.value];
});

watch(
  () => valueInternal.value,
  () => {
    if (!valueInternal.value) {
      hints.value = localHints.value;
    }
  },
);

// @ts-ignore Vuetify component needs `null` instead of empty string initially
valueInternal.value = props.modelValue || null;

onMounted(async () => {
  previousValueInternal.value = props.modelValue;
  try {
    await _onTypeahead();
  } catch (e) {}
  hints.value = typeaheadHints.value;

  // Initially, set focus on the input, but hide menu.
  if (props.autoFocus) {
    setTimeout(() => {
      searchInput.value?.focus();
      menu.value = false;
    }, 0);
  }

  // https://www.learnrxjs.io/learn-rxjs/recipes/type-ahead
  if (searchInput.value) {
    fromEvent(searchInput.value?.$el, "input")
      .pipe(
        tap(() => {
          isFetchingHints.value = !!valueInternal.value;
          // Show hints from local history while the database ones load
          hints.value = localHints.value;
          menu.value = true;
          if (props.isEager) {
            emit("update:model-value", valueInternal.value);
          }
        }),
        debounceTime(typeaheadDebounceTime),
        map((e: any) => e.target.value),
        switchMap(() => from(_onTypeahead())),
      )
      .subscribe(() => {
        _handleTypeahead();
      });
  }
});

function onSearch() {
  previousValueInternal.value = valueInternal.value;
  menu.value = false;
  emit("update:model-value", valueInternal.value);
}

async function onHintSelected(event: PointerEvent, hint: IHint) {
  // Ignore clicks on the action buttons
  if (
    // @ts-ignore
    event.target?.classList.contains("mdi-close")
  ) {
    return;
  }

  valueInternal.value = hint.key;
  isFetchingHints.value = !!valueInternal.value;
  onSearch();
  emit("hint-selected", valueInternal.value);
}

async function onHintRight(_event: PointerEvent, hint: IHint) {
  valueInternal.value = hint.key;
  searchInput.value?.focus();
}

function deleteHint(hint: IHint) {
  SearchHistory.deleteHint(hint.key);
  hints.value = typeaheadHints.value;
}

async function _onTypeahead() {
  if (!valueInternal.value?.trim?.()) {
    isFetchingHints.value = false;
    hints.value = typeaheadHints.value;
    return;
  }

  try {
    previousValueInternal.value = valueInternal.value;
    rawDbHints.value = await Search.typeahead({
      term: valueInternal.value,
      field: props.targetField,
    });
    isFetchingHints.value = false;
  } catch (e) {
    console.log(e);
  }
}

function boldStart(title: string, startStr: string) {
  if (title.indexOf(startStr) >= 0) {
    return title.replace(startStr, `<b>${startStr}</b>`);
  }
  return title;
}

function _handleTypeahead() {
  hints.value = typeaheadHints.value;
  if (valueInternal.value) {
    isFetchingHints.value = false;
  }
}
</script>

<style lang="scss" scoped>
.cd-home-search {
  background: #ddd;
}

.search-container {
  max-width: 45rem;
}
</style>
