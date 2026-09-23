<script lang="ts">
	import { api } from '$lib/api/client';
	import { showToast } from '$lib/stores/ui';
	import { autoTighteningProgress } from '$lib/stores/tightening';
	import { Section, Button, FormField, Badge } from '$lib/components/ui';
	import { formatBatchCounter, formatErrorMessage } from '$lib/utils';

	let config = $state({
		interval_ms: 1000,
		duration_ms: 500,
		failure_rate: 0.0
	});
	let isLoading = $state(false);

	async function handleToggle() {
		isLoading = true;
		try {
			if ($autoTighteningProgress.running) {
				await api.stopAutoTightening();
				showToast({ type: 'success', message: '已停止自动循环拧紧！' });
			} else {
				await api.startAutoTightening(config);
				showToast({ type: 'success', message: '已启动自动循环拧紧！' });
			}
		} catch (error) {
			const action = $autoTighteningProgress.running ? '停止' : '启动';
			showToast({ type: 'error', message: formatErrorMessage(`${action}自动拧紧失败`, error) });
		} finally {
			isLoading = false;
		}
	}
</script>

<Section
	title="自动循环拧紧"
	description="设定循环执行周期与失败率，持续模拟生产线拧紧节拍与进度。"
>
	<!-- Status Display -->
	<div class="rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-4">
		<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
			<div>
				<p class="text-xs uppercase tracking-wide text-surface-600-300-token">运行状态</p>
				<div class="mt-2">
					<Badge
						variant={$autoTighteningProgress.running ? 'filled-success' : 'soft'}
					>
						{$autoTighteningProgress.running ? '运行中' : '已停止'}
					</Badge>
				</div>
			</div>
			{#if $autoTighteningProgress.target_size > 0 || $autoTighteningProgress.counter > 0}
				<div class="text-sm text-surface-600-300-token">
					<p class="font-semibold">当前批次进度</p>
					<p class="text-surface-600-300-token">
						{formatBatchCounter(
							$autoTighteningProgress.counter,
							$autoTighteningProgress.target_size
						)}
					</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Configuration Form -->
	<form
		onsubmit={(e) => {
			e.preventDefault();
			handleToggle();
		}}
		class="space-y-6"
	>
		<div class="grid gap-4 md:grid-cols-3">
			<FormField
				label="循环间隔 (毫秒)"
				type="number"
				bind:value={config.interval_ms}
				min={100}
				step={100}
			/>
			<FormField
				label="拧紧耗时 (毫秒)"
				type="number"
				bind:value={config.duration_ms}
				min={100}
				step={100}
			/>
			<FormField
				label="超差/失败概率 (0.0 – 1.0)"
				type="number"
				bind:value={config.failure_rate}
				min={0}
				max={1}
				step={0.1}
			/>
		</div>

		<div class="flex justify-end">
			<Button
				type="submit"
				variant={$autoTighteningProgress.running ? 'filled-error' : 'filled-primary'}
				disabled={isLoading}
				class="sm:w-auto"
			>
				{#if isLoading}
					{$autoTighteningProgress.running ? '正在停止...' : '正在启动...'}
				{:else}
					{$autoTighteningProgress.running ? '停止自动循环' : '启动自动循环'}
				{/if}
			</Button>
		</div>
	</form>
</Section>
