<script lang="ts">
	import { api } from '$lib/api/client';
	import { showToast } from '$lib/stores/ui';
	import { deviceState } from '$lib/stores/device';
	import { Section, Button, FormField } from '$lib/components/ui';
	import { toPercentage, toRate, formatErrorMessage } from '$lib/utils';
	import { onMount } from 'svelte';

	let config = $state({
		enabled: false,
		connection_health: 100,
		packet_loss_rate: 0.0,
		delay_min_ms: 0,
		delay_max_ms: 0,
		corruption_rate: 0.0,
		force_disconnect_rate: 0.0
	});

	let showAdvanced = $state(false);
	let isUpdatingHealth = $state(false);
	let isUpdatingAdvanced = $state(false);

	// Compute connection status based on health
	const connectionStatus = $derived((() => {
		const health = config.connection_health;
		if (health === 100) return { label: '极佳 (Perfect)', color: 'text-success-500' };
		if (health >= 75) return { label: '健康 (Healthy)', color: 'text-success-400' };
		if (health >= 50) return { label: '降级 (Degraded)', color: 'text-warning-500' };
		if (health >= 25) return { label: '不稳定 (Unstable)', color: 'text-warning-600' };
		return { label: '严重受损 (Severe)', color: 'text-error-500' };
	})());

	// Compute slider color based on health
	const sliderColor = $derived((() => {
		const health = config.connection_health;
		if (health >= 75) return 'accent-success-500';
		if (health >= 50) return 'accent-warning-500';
		if (health >= 25) return 'accent-warning-600';
		return 'accent-error-500';
	})());

	async function handleUpdateHealth() {
		isUpdatingHealth = true;
		try {
			const response = await api.updateFailureConfig({
				connection_health: config.connection_health
			});
			showToast({
				type: 'success',
				message: '通信健康度与故障注入配置已更新！'
			});

			// Update local config with confirmed state from backend
			config = {
				enabled: response.config.enabled,
				connection_health: response.config.connection_health,
				packet_loss_rate: toPercentage(response.config.packet_loss_rate),
				delay_min_ms: response.config.delay_min_ms,
				delay_max_ms: response.config.delay_max_ms,
				corruption_rate: toPercentage(response.config.corruption_rate),
				force_disconnect_rate: toPercentage(response.config.force_disconnect_rate)
			};

			// Refresh device state
			const state = await api.getDeviceState();
			deviceState.set(state);
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('更新故障注入配置失败', error) });
		} finally {
			isUpdatingHealth = false;
		}
	}

	async function handleUpdateAdvanced() {
		isUpdatingAdvanced = true;
		try {
			const response = await api.updateFailureConfig({
				enabled: config.enabled,
				packet_loss_rate: toRate(config.packet_loss_rate),
				delay_min_ms: config.delay_min_ms,
				delay_max_ms: config.delay_max_ms,
				corruption_rate: toRate(config.corruption_rate),
				force_disconnect_rate: toRate(config.force_disconnect_rate)
			});
			showToast({
				type: 'success',
				message: '高级故障注入参数已更新！'
			});

			// Update local config with confirmed state from backend
			config = {
				enabled: response.config.enabled,
				connection_health: response.config.connection_health,
				packet_loss_rate: toPercentage(response.config.packet_loss_rate),
				delay_min_ms: response.config.delay_min_ms,
				delay_max_ms: response.config.delay_max_ms,
				corruption_rate: toPercentage(response.config.corruption_rate),
				force_disconnect_rate: toPercentage(response.config.force_disconnect_rate)
			};
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('更新高级故障注入配置失败', error) });
		} finally {
			isUpdatingAdvanced = false;
		}
	}

	async function handleReset() {
		config.connection_health = 100;
		await handleUpdateHealth();
	}

	// Initialize from device state on mount
	onMount(() => {
		if ($deviceState) {
			config = {
				enabled: $deviceState.failure_config.enabled,
				connection_health: $deviceState.failure_config.connection_health,
				packet_loss_rate: toPercentage($deviceState.failure_config.packet_loss_rate),
				delay_min_ms: $deviceState.failure_config.delay_min_ms,
				delay_max_ms: $deviceState.failure_config.delay_max_ms,
				corruption_rate: toPercentage($deviceState.failure_config.corruption_rate),
				force_disconnect_rate: toPercentage($deviceState.failure_config.force_disconnect_rate)
			};
		}
	});
</script>

<Section
	title="通信异常与故障注入模拟"
	description="调节网络连接健康度，模拟网络延迟、丢包或随机异常，测试工控上位机/MES 客户端的容错重试机制。"
>
	<!-- Status Display -->
	<div class="rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-4">
		<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
			<div>
				<p class="text-xs uppercase tracking-wide text-surface-600-300-token">
					通信状态判定
				</p>
				<p class="mt-2 text-xl font-semibold {connectionStatus.color}">
					{connectionStatus.label}
				</p>
			</div>
			{#if config.enabled && config.connection_health < 100}
				<div
					class="flex items-start gap-2 rounded-md bg-surface-100-800-token p-3 text-sm text-warning-600"
				>
					<span aria-hidden="true">⚠️</span>
					<span>故障注入处于生效状态，TCP 连接可能会出现丢包或延迟。</span>
				</div>
			{/if}
		</div>
	</div>

	<!-- Connection Health Slider -->
	<div class="space-y-3">
		<label
			for="connection-health-slider"
			class="flex items-center justify-between text-sm font-semibold text-surface-600-300-token"
		>
			<span>连接健康度 (Health)</span>
			<span class="{connectionStatus.color} text-lg">
				{config.connection_health}%
			</span>
		</label>
		<div class="flex items-center gap-3">
			<span class="text-xs uppercase tracking-wide text-surface-600-300-token w-10 text-left"
				>0%</span
			>
			<input
				id="connection-health-slider"
				type="range"
				class="flex-1 {sliderColor}"
				bind:value={config.connection_health}
				min="0"
				max="100"
				step="1"
				onchange={handleUpdateHealth}
			/>
			<span class="text-xs uppercase tracking-wide text-surface-600-300-token w-10 text-right"
				>100%</span
			>
		</div>
		<div class="grid grid-cols-5 text-xs text-surface-600-300-token">
			<span>严重受损</span>
			<span class="text-center">不稳定</span>
			<span class="text-center">性能降级</span>
			<span class="text-center">良好</span>
			<span class="text-right">极佳</span>
		</div>
		<div class="flex justify-end">
			<Button variant="ghost-surface" onclick={handleReset} disabled={isUpdatingHealth} class="btn-sm">
				{isUpdatingHealth ? '重置中...' : '重置为 100% (完全健康)'}
			</Button>
		</div>
	</div>

	<!-- Current Configuration Display -->
	<div
		class="rounded-lg border border-dashed border-surface-200-700-token bg-surface-100-800-token p-4 text-sm"
	>
		<p class="font-semibold">当前注入参数详情</p>
		<dl class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">
					丢包率 (Packet Loss)
				</dt>
				<dd class="mt-1 font-semibold">
					{config.packet_loss_rate.toFixed(1)}%
				</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">
					延迟范围 (Delay Range)
				</dt>
				<dd class="mt-1 font-semibold">
					{config.delay_min_ms}-{config.delay_max_ms} ms
				</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">
					报文损坏率 (Corruption)
				</dt>
				<dd class="mt-1 font-semibold">
					{config.corruption_rate.toFixed(1)}%
				</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">
					强行断开率 (Disconnect)
				</dt>
				<dd class="mt-1 font-semibold">
					{config.force_disconnect_rate.toFixed(1)}%
				</dd>
			</div>
		</dl>
	</div>

	<!-- Advanced Settings -->
	<details
		class="rounded-lg border border-surface-200-700-token p-4"
		bind:open={showAdvanced}
	>
		<summary
			class="cursor-pointer text-sm font-semibold text-primary-500 hover:text-primary-600"
		>
			高级自定义参数 (手动覆盖配置)
		</summary>
		<div class="mt-4 space-y-4">
			<label
				class="flex items-center gap-3 rounded-lg bg-surface-100-800-token p-3 cursor-pointer"
			>
				<input type="checkbox" class="checkbox" bind:checked={config.enabled} />
				<span class="font-semibold">启用底层故障注入参数</span>
			</label>

			<FormField
				label="丢包率 (%)"
				type="number"
				bind:value={config.packet_loss_rate}
				min={0}
				max={100}
				step={0.1}
			/>

			<div class="grid gap-4 md:grid-cols-2">
				<FormField
					label="最小网络延迟 (ms)"
					type="number"
					bind:value={config.delay_min_ms}
					min={0}
					step={10}
				/>
				<FormField
					label="最大网络延迟 (ms)"
					type="number"
					bind:value={config.delay_max_ms}
					min={0}
					step={10}
				/>
			</div>

			<FormField
				label="报文损坏率 (%)"
				type="number"
				bind:value={config.corruption_rate}
				min={0}
				max={100}
				step={0.1}
			/>

			<FormField
				label="强制断线概率 (%)"
				type="number"
				bind:value={config.force_disconnect_rate}
				min={0}
				max={100}
				step={0.1}
			/>

			<Button onclick={handleUpdateAdvanced} disabled={isUpdatingAdvanced} class="w-full sm:w-auto">
				{isUpdatingAdvanced ? '正在应用...' : '应用高级配置'}
			</Button>
		</div>
	</details>
</Section>
