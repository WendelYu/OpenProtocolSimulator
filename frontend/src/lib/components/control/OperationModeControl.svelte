<script lang="ts">
	import { api } from '$lib/api/client';
	import { deviceState } from '$lib/stores/device';
	import { showToast } from '$lib/stores/ui';
	import { refreshDeviceState } from '$lib/stores/websocket';
	import { formatErrorMessage } from '$lib/utils';
	import { Badge, Button, Section } from '$lib/components/ui';
	import type { OperationMode, OperationModeRequest } from '$lib/types';

	let selectedMode: OperationMode = $state('pset');
	let isApplying = $state(false);
	let observedMode: OperationMode | null = null;

	const modes: { id: OperationMode; label: string; description: string }[] = [
		{ id: 'pset', label: '参数集 (PSET)', description: '由选定参数集控制拧紧' },
		{ id: 'batch', label: '批次 (Batch)', description: '启用 MID 0019 批次计数与跟踪' },
		{ id: 'job', label: '作业 (Job)', description: '由作业序列步骤统一控制' }
	];

	const changingRunningJob = $derived(
		$deviceState?.operation_mode === 'job' &&
			$deviceState.current_job_status === 'running' &&
			String(selectedMode) !== 'job'
	);

	$effect(() => {
		const state = $deviceState;
		if (!state) return;
		if (state.operation_mode !== observedMode) {
			observedMode = state.operation_mode;
			selectedMode = state.operation_mode;
		}
	});

	async function applyMode() {
		const request: OperationModeRequest = { mode: selectedMode };

		isApplying = true;
		try {
			const response = await api.setOperationMode(request);
			await refreshDeviceState();
			showToast({ type: 'success', message: response.message });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('切换运行模式失败', error) });
		} finally {
			isApplying = false;
		}
	}
</script>

<Section
	title="运行模式切换"
	description="选择控制器运行模式以及支持的 Open Protocol 专属指令集。"
>
	<div class="grid gap-3 md:grid-cols-3">
		{#each modes as mode}
			<button
				type="button"
				class="rounded-lg border p-4 text-left transition-colors"
				class:border-primary-500={selectedMode === mode.id}
				class:bg-primary-500={selectedMode === mode.id}
				class:text-white={selectedMode === mode.id}
				class:border-surface-200-700-token={selectedMode !== mode.id}
				class:bg-surface-100-800-token={selectedMode !== mode.id}
				onclick={() => (selectedMode = mode.id)}
				aria-pressed={selectedMode === mode.id}
			>
				<span class="block font-semibold">{mode.label}</span>
				<span class="mt-1 block text-sm opacity-75">{mode.description}</span>
			</button>
		{/each}
	</div>

	{#if selectedMode === 'batch'}
		<p class="text-sm opacity-70">
			批次模式 (Batch mode)：根据 MID 0019 设定的批次大小跟踪拧紧计数；未配置批次前不计入批次。此时作业选择指令 (MID 0038) 将被错误码 20 拒绝。
		</p>
	{:else if selectedMode === 'job'}
		<p class="text-sm opacity-70">
			作业模式 (Job mode)：支持作业选择 (MID 0038) 与作业批次递增 (MID 0128)。在作业驱动期间，直接选择参数集 (MID 0018) 将被错误码 03 拒绝，批次配置 (MID 0019-0020) 将被错误码 01 拒绝。
		</p>
	{:else}
		<p class="text-sm opacity-70">
			参数集模式 (PSET mode)：执行单次拧紧。根据协议规范，通过 MID 0019 设置批次大小时会自动切换至批次模式。作业选择 (MID 0038) 将被错误码 20 拒绝。数据上传与订阅在所有模式下均可正常响应。
		</p>
	{/if}

	{#if changingRunningJob}
		<p class="rounded-md bg-warning-50 p-3 text-sm text-warning-700 dark:bg-warning-900/20">
			切换此模式将放弃当前正在执行的作业。
		</p>
	{/if}

	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div class="flex items-center gap-2 text-sm">
			<span class="opacity-70">当前运行模式:</span>
			<Badge variant="soft">{$deviceState?.operation_mode?.toUpperCase() ?? '加载中'}</Badge>
			{#if $deviceState?.operation_mode === 'batch'}
				{#if $deviceState.batch_size > 0}
					<span class="opacity-70">
						{$deviceState.batch_counter} / {$deviceState.batch_size}
					</span>
				{:else}
					<span class="opacity-70">未配置批次</span>
				{/if}
			{/if}
		</div>
		<Button onclick={applyMode} disabled={isApplying}>
			{isApplying ? '正在应用...' : '应用此模式'}
		</Button>
	</div>
</Section>
