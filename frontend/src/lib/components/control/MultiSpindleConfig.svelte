<script lang="ts">
	import { api } from '$lib/api/client';
	import { showToast } from '$lib/stores/ui';
	import { deviceState } from '$lib/stores/device';
	import { Section, Button, FormField } from '$lib/components/ui';
	import { formatErrorMessage } from '$lib/utils';
	import { onMount } from 'svelte';

	let config = $state({
		enabled: false,
		spindle_count: 4,
		sync_id: 1
	});
	let isSaving = $state(false);

	async function handleSubmit() {
		isSaving = true;
		try {
			await api.configureMultiSpindle(config);
			showToast({
				type: 'success',
				message: `多轴同步模式已${config.enabled ? '启用' : '禁用'}！`
			});

			// Refresh device state to ensure UI reflects backend state
			const state = await api.getDeviceState();
			deviceState.set(state);

			// Update form with confirmed state from backend
			config = {
				enabled: state.multi_spindle_config.enabled,
				spindle_count: state.multi_spindle_config.spindle_count,
				sync_id: state.multi_spindle_config.sync_id
			};
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('配置多轴模式失败', error) });
		} finally {
			isSaving = false;
		}
	}

	// Initialize from device state on mount
	onMount(() => {
		if ($deviceState) {
			config = {
				enabled: $deviceState.multi_spindle_config.enabled,
				spindle_count: $deviceState.multi_spindle_config.spindle_count,
				sync_id: $deviceState.multi_spindle_config.sync_id
			};
		}
	});
</script>

<Section
	title="多轴同步拧紧配置 (Multi-Spindle)"
	description="启用多轴同步拧紧并设置轴数与同步组 ID。"
>
	<form
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
		class="space-y-4"
	>
		<label
			class="flex items-center gap-3 rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-3 cursor-pointer"
		>
			<input type="checkbox" class="checkbox" bind:checked={config.enabled} />
			<span class="block">
				<p class="font-semibold">启用多轴同步模式</p>
				<p class="text-sm opacity-70">
					启用后，模拟器将按同步组 ID 一同产生所有分轴的拧紧曲线与数据。
				</p>
			</span>
		</label>

		{#if config.enabled}
			<div class="grid gap-4 md:grid-cols-2">
				<FormField
					label="同步轴数 (2-16)"
					type="number"
					bind:value={config.spindle_count}
					min={2}
					max={16}
				/>
				<FormField
					label="同步组 ID (Sync ID)"
					type="number"
					bind:value={config.sync_id}
					min={1}
				/>
			</div>
		{/if}

		<div class="flex justify-end">
			<Button type="submit" disabled={isSaving} class="sm:w-auto">
				{isSaving ? '正在保存...' : '应用多轴配置'}
			</Button>
		</div>
	</form>
</Section>
