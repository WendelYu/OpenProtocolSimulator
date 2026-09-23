<script lang="ts">
	import { api } from '$lib/api/client';
	import { deviceState } from '$lib/stores/device';
	import { showToast } from '$lib/stores/ui';
	import { Section, Button, FormField } from '$lib/components/ui';
	import { getPsetTargets, formatErrorMessage, validateRange } from '$lib/utils';
	import type { Pset, TighteningRequest } from '$lib/types';
	import { refreshDeviceState } from '$lib/stores/websocket';
	import { setLatestCurves } from '$lib/stores/tightening';

	interface Props {
		currentPset: Pset | undefined;
	}

	let { currentPset }: Props = $props();

	let usePsetValues = $state(true);
	let resultMode: 'auto' | 'ok' | 'nok' = $state('auto');
	let tighteningPayload = $state({
		torque: 12.5,
		angle: 40.0
	});
	let isSubmitting = $state(false);
	let validationErrors = $state({
		torque: '',
		angle: ''
	});

	const currentPsetTargets = $derived(
		currentPset ? getPsetTargets(currentPset) : null
	);
	const isToolEnabled = $derived($deviceState?.tool_enabled ?? true);
	const isJobRunning = $derived($deviceState?.current_job_status === 'running');
	const isCompletedJob = $derived(
		$deviceState?.current_job_status === 'ok' || $deviceState?.current_job_status === 'nok'
	);

	const isFormValid = $derived(
		usePsetValues || (!validationErrors.torque && !validationErrors.angle)
	);

	// Real-time validation using $effect
	$effect(() => {
		if (isJobRunning) usePsetValues = true;
		if (!usePsetValues) {
			validationErrors.torque = validateRange(
				tighteningPayload.torque,
				0,
				100,
				'Torque'
			);
			validationErrors.angle = validateRange(
				tighteningPayload.angle,
				0,
				360,
				'Angle'
			);
		} else {
			// Clear errors when using PSET values
			validationErrors.torque = '';
			validationErrors.angle = '';
		}
	});

	async function handleSubmit() {
		if (!isToolEnabled) {
			showToast({
				type: 'warning',
				message: '工具已被禁用。请在上位机或模拟器中启用工具后再模拟拧紧。'
			});
			return;
		}

		isSubmitting = true;
		try {
			let payload: TighteningRequest = {};

			if (!usePsetValues) {
				payload.torque = tighteningPayload.torque;
				payload.angle = tighteningPayload.angle;
			}
			if (resultMode !== 'auto') payload.ok = resultMode === 'ok';

			const res = await api.simulateTightening(payload);
			if (res.result && res.torque_curve && res.angle_curve) {
				setLatestCurves({
					result_id: res.result.tightening_id ?? 1,
					timestamp: res.result.timestamp,
					is_ok: res.result.tightening_status,
					actual_torque: res.result.torque,
					actual_angle: res.result.angle,
					torque_curve: res.torque_curve,
					angle_curve: res.angle_curve
				});
			}
			await refreshDeviceState();
			showToast({ type: 'success', message: '已成功模拟一次拧紧！' });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('模拟拧紧失败', error) });
		} finally {
			isSubmitting = false;
		}
	}

	async function setDirection(dir: 'CW' | 'CCW') {
		try {
			await api.setToolDirection(dir);
			await refreshDeviceState();
			showToast({ type: 'success', message: `工具转向已切换为 ${dir === 'CW' ? '正转/紧固 (CW)' : '反转/松开 (CCW)'}` });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('切换转向失败', error) });
		}
	}
</script>

<Section
	title="单次拧紧模拟"
	description="根据当前生效参数集或手动设定扭矩/角度，触发一次完整的拧紧循环。"
>
	<form
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
		class="space-y-6"
	>
		{#if !isToolEnabled}
			<div
				class="flex items-start gap-2 rounded-md bg-surface-100-800-token p-3 text-sm text-warning-600"
			>
				<span aria-hidden="true">⚠️</span>
				<span>工具当前处于禁用状态 (Disabled)，单次拧紧模拟不可用。请在上位机或控制端启用。</span>
			</div>
		{/if}
		{#if isJobRunning}
			<div class="rounded-md bg-warning-50 p-3 text-sm text-warning-700 dark:bg-warning-900/20">
				作业模式 (JobMode) 正在运行中，当前参数集、扭矩、角度及批次由作业步骤驱动。仍可在此强制判定 OK/NOK。
			</div>
		{:else if isCompletedJob}
			<div class="rounded-md bg-surface-100-800-token p-3 text-sm">
				当前作业已执行完毕。请先重新启动作业或退出作业模式后再进行拧紧。
			</div>
		{/if}

		<!-- Tool Direction & Switch Control -->
		<div class="flex flex-wrap items-center justify-between gap-4 p-3 rounded-lg border border-surface-200-700-token bg-surface-100-800-token">
			<div class="text-sm">
				<span class="font-medium text-surface-900 dark:text-surface-100">工具转向 (MID 0216/0217):</span>
				<span class="ml-2 font-mono text-xs px-2 py-0.5 rounded bg-surface-200 dark:bg-surface-700">
					{$deviceState?.tool_direction === 'CCW' ? '逆时针/松开 (CCW)' : '顺时针/紧固 (CW)'}
				</span>
			</div>
			<div class="inline-flex rounded-lg border border-surface-200-700-token p-1 gap-1">
				<button
					type="button"
					class="px-3 py-1 text-xs font-semibold rounded transition-colors"
					class:bg-primary-500={$deviceState?.tool_direction !== 'CCW'}
					class:text-white={$deviceState?.tool_direction !== 'CCW'}
					onclick={() => setDirection('CW')}
				>
					顺时针 (CW)
				</button>
				<button
					type="button"
					class="px-3 py-1 text-xs font-semibold rounded transition-colors"
					class:bg-primary-500={$deviceState?.tool_direction === 'CCW'}
					class:text-white={$deviceState?.tool_direction === 'CCW'}
					onclick={() => setDirection('CCW')}
				>
					逆时针 (CCW)
				</button>
			</div>
		</div>

		<!-- Toggle between PSET and Manual -->
		<div
			class="inline-flex rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-1"
		>
			<button
				type="button"
				class="px-4 py-2 text-sm font-semibold transition-colors rounded"
				class:bg-primary-500={usePsetValues}
				class:text-white={usePsetValues}
				class:opacity-60={!usePsetValues}
				onclick={() => (usePsetValues = true)}
			>
				使用参数集 (PSET) 预设值
			</button>
			<button
				type="button"
				class="px-4 py-2 text-sm font-semibold transition-colors rounded"
				class:bg-primary-500={!usePsetValues}
				class:text-white={!usePsetValues}
				class:opacity-60={usePsetValues}
				onclick={() => (usePsetValues = false)}
				disabled={isJobRunning}
			>
				手动设定数值
			</button>
		</div>

		{#if usePsetValues}
			<!-- PSET Mode -->
			<div
				class="rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-4"
			>
				{#if currentPsetTargets}
					<p class="text-xs uppercase tracking-wide text-surface-600-300-token">
						参数集设定目标
					</p>
					<div class="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
						<div>
							<p class="text-sm opacity-70">目标扭矩</p>
							<p class="text-xl font-semibold">
								{currentPsetTargets.torque} N·m
							</p>
						</div>
						<div>
							<p class="text-sm opacity-70">目标角度</p>
							<p class="text-xl font-semibold">
								{currentPsetTargets.angle}°
							</p>
						</div>
					</div>
					<p class="mt-3 text-sm opacity-70">
						拧紧结果将由状态机及公差范围自动计算判定。
					</p>
				{:else}
					<p class="text-sm opacity-70">请选择一个参数集以预览其设定目标。</p>
				{/if}
			</div>
		{:else}
			<!-- Manual Override Mode -->
			<div class="grid gap-4 md:grid-cols-2">
				<FormField
					label="扭矩 (N·m)"
					type="number"
					bind:value={tighteningPayload.torque}
					step="0.1"
					min={0}
					max={100}
					error={validationErrors.torque}
				/>
				<FormField
					label="角度 (°)"
					type="number"
					bind:value={tighteningPayload.angle}
					step="0.1"
					min={0}
					max={360}
					error={validationErrors.angle}
				/>
			</div>

		{/if}

		<FormField
			label="判定结果模式"
			type="select"
			bind:value={resultMode}
			options={[
				{ value: 'auto', label: '自动计算 (基于公差标准)' },
				{ value: 'ok', label: '强制判定合格 (OK)' },
				{ value: 'nok', label: '强制判定超差 (NOK)' }
			]}
			help={isJobRunning ? '作业模式运行中仍可强制设定合格/超差判定结果。' : undefined}
		/>

		<Button
			type="submit"
			disabled={isSubmitting || !isFormValid || !isToolEnabled || isCompletedJob}
			class="w-full sm:w-auto"
		>
			{isSubmitting ? '正在执行模拟...' : '模拟拧紧'}
		</Button>
	</form>
</Section>
