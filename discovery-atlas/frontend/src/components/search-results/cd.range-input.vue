<template>
  <div>
    <!-- <v-checkbox
      :model-value="isActive"
      @update:model-value="$emit('update:is-active', $event)"
      :label="label"
      density="compact"
      hide-details
      color="primary"
    /> -->
    <v-range-slider
      :model-value="modelValue"
      @update:model-value="$emit('update:model-value', $event)"
      @end="$emit('end')"
      :class="{ 'grayed-out': !isActive }"
      :min="min"
      :max="max"
      color="primary"
      class="mb-1"
      step="1"
      track-size="1"
      thumb-size="15"
      hide-details
    />
    <v-row :class="{ 'grayed-out': !isActive }">
      <v-col>
        <v-text-field
          :model-value="modelValue[0]"
          @update:model-value="modelValue[0] = +$event"
          type="number"
          @blur="
            $emit('update:model-value', range);
            $emit('end');
          "
          @keyup.enter="
            $emit('update:model-value', range);
            $emit('end');
          "
          :min="min"
          :max="max"
          label="Start"
          variant="outlined"
          density="compact"
          focusable
        />
      </v-col>

      <v-col>
        <v-text-field
          :model-value="modelValue[1]"
          @update:model-value="modelValue[1] = +$event"
          type="number"
          @blur="
            $emit('update:model-value', range);
            $emit('end');
          "
          @keyup.enter="
            $emit('update:model-value', range);
            $emit('end');
          "
          :min="min"
          :max="max"
          label="End"
          variant="outlined"
          density="compact"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
defineEmits(["end", "update:model-value", "update:is-active"]);

const props = withDefaults(
  defineProps<{
    modelValue: [number, number];
    isActive: boolean;
    label: string;
    // Optional so callers can bind a possibly-undefined source (e.g. Filter);
    // defaults keep the internal numeric math well-typed.
    min?: number;
    max?: number;
  }>(),
  { min: 0, max: 0 },
);

const range = computed(() => {
  // Check date range cross over
  if (props.modelValue[0] > props.modelValue[1]) {
    // swap values
    const temp = props.modelValue[0];
    props.modelValue[0] = props.modelValue[1];
    props.modelValue[1] = temp;
  }
  // Clip values
  return [
    Math.max(props.min, props.modelValue[0]),
    Math.min(props.max, props.modelValue[1]),
  ];
});
</script>

<style lang="scss" scoped>
.grayed-out {
  opacity: 0.55;
}
</style>
