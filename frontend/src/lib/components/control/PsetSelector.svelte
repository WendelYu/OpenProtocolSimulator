<script lang="ts">
	import { deviceState } from '$lib/stores/device';
	import { api } from '$lib/api/client';
	import { showToast } from '$lib/stores/ui';
	import { Section, Badge } from '$lib/components/ui';
	import { getPsetTargets, formatErrorMessage } from '$lib/utils';
	import type { Pset } from '$lib/types';

	interface Props {
		psets: Pset[];
	}

	let { psets }: Props = $props();

	const currentPset = $derived(
		psets.find((p) => p.id === $deviceState?.current_pset_id)
	);

	const currentPsetTargets = $derived(
		currentPset ? getPsetTargets(currentPset) : null
	);
	const psetSelectionDisabled = $derived($deviceState?.operation_mode === 'job');

	async function handleSelectPset(psetId: number) {
		if (psetSelectionDisabled) return;
		try {
			await api.selectPset(psetId);
			showToast({ type: 'success', message: `已选择参数集 PSET ${psetId}！` });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('选择参数集失败', error) });
		}
	}
</script>

<Section
	title="参数集 (PSET) 选择"
	description="选择生效的拧紧参数集以加载其对应的目标扭矩与角度限制"
>
	<div class="grid gap-6 lg:grid-cols-2">
		<label class="label">
			<span>选择参数集</span>
			<select
				class="select"
				value={$deviceState?.current_pset_id || ''}
				onchange={(e) => handleSelectPset(Number(e.currentTarget.value))}
				disabled={psetSelectionDisabled}
			>
				{#each psets as pset}
					<option value={pset.id}>
						{pset.name} (编号 {pset.id})
					</option>
				{/each}
			</select>
		</label>

		<div
			class="rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-4"
		>
			{#if currentPsetTargets}
				<p class="text-xs uppercase tracking-wide text-surface-600-300-token mb-3">
					预设目标指标
				</p>
				<dl class="grid grid-cols-2 gap-4">
					<div>
						<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">
							目标扭矩
						</dt>
						<dd class="mt-1 font-semibold">
							{currentPsetTargets.torque} N·m
						</dd>
					</div>
					<div>
						<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">
							目标角度
						</dt>
						<dd class="mt-1 font-semibold">
							{currentPsetTargets.angle}°
						</dd>
					</div>
				</dl>
			{:else}
				<p class="text-sm opacity-70">未选择参数集。请选择一个参数集以预览目标。</p>
			{/if}
		</div>
	</div>
	{#if psetSelectionDisabled}
		<p class="mt-4 text-sm text-warning-600">
			当前处于作业模式 (Job mode)，由作业步骤控制参数集，手动选择已暂时禁用。
		</p>
	{/if}
</Section>
