<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import { latestCurves, setLatestCurves } from '$lib/stores/tightening';
	import { showToast } from '$lib/stores/ui';
	import type { LatestCurves } from '$lib/types';

	type ChartMode = 'torque_time' | 'angle_time' | 'dual_time' | 'torque_angle';

	let chartMode: ChartMode = $state('dual_time');
	let canvasElement: HTMLCanvasElement | null = $state(null);
	let containerElement: HTMLDivElement | null = $state(null);
	let hoveredSample: {
		index: number;
		timeMs: number;
		torque: number;
		angle: number;
		x: number;
		y: number;
	} | null = $state(null);

	let curves: LatestCurves | null = $derived($latestCurves);

	// Load initial latest curve if not present
	onMount(() => {
		if (!curves) {
			api.getLatestCurve().then((data) => {
				if (data) setLatestCurves(data);
			}).catch(() => {});
		}

		const resizeObserver = new ResizeObserver(() => {
			renderChart();
		});

		if (containerElement) {
			resizeObserver.observe(containerElement);
		}

		return () => {
			resizeObserver.disconnect();
		};
	});

	$effect(() => {
		// Re-render whenever curves or chartMode changes
		if (curves || !curves) {
			renderChart();
		}
	});

	function getCurveData() {
		if (!curves) return null;
		const tCurve = curves.torque_curve;
		const aCurve = curves.angle_curve;
		const count = Math.min(tCurve.samples.length, aCurve.samples.length);
		const interval = tCurve.time_interval_ms || 2;
		const tCoeff = tCurve.coefficient || 100;
		const aCoeff = aCurve.coefficient || 100;

		const points = [];
		let maxT = 0.1;
		let maxA = 0.1;
		let peakTIdx = 0;
		let peakAIdx = 0;

		for (let i = 0; i < count; i++) {
			const timeMs = i * interval;
			const torque = Number((tCurve.samples[i] / tCoeff).toFixed(2));
			const angle = Number((aCurve.samples[i] / aCoeff).toFixed(1));
			if (torque > maxT) {
				maxT = torque;
				peakTIdx = i;
			}
			if (angle > maxA) {
				maxA = angle;
				peakAIdx = i;
			}
			points.push({ index: i, timeMs, torque, angle });
		}

		// Snug point heuristic: point around 30% of max torque during rise phase
		let snugIdx = Math.floor(count * 0.35);
		for (let i = 0; i < count; i++) {
			if (points[i].torque >= maxT * 0.25) {
				snugIdx = i;
				break;
			}
		}

		return {
			points,
			count,
			interval,
			totalTimeMs: (count - 1) * interval,
			maxTorque: Math.max(maxT * 1.15, 1.0),
			maxAngle: Math.max(maxA * 1.15, 10.0),
			peakTIdx,
			peakAIdx,
			snugIdx
		};
	}

	function renderChart() {
		if (!canvasElement || !containerElement) return;
		const ctx = canvasElement.getContext('2d');
		if (!ctx) return;

		const dpr = window.devicePixelRatio || 1;
		const rect = containerElement.getBoundingClientRect();
		const width = Math.floor(rect.width);
		const height = 340;

		canvasElement.width = width * dpr;
		canvasElement.height = height * dpr;
		canvasElement.style.width = `${width}px`;
		canvasElement.style.height = `${height}px`;

		ctx.save();
		ctx.scale(dpr, dpr);

		// Clear canvas
		ctx.clearRect(0, 0, width, height);

		const isDark = document.documentElement.classList.contains('dark') || true;
		const gridColor = isDark ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.07)';
		const textColor = isDark ? '#94a3b8' : '#64748b';

		const padLeft = 55;
		const padRight = chartMode === 'dual_time' ? 55 : 25;
		const padTop = 30;
		const padBottom = 40;
		const plotW = width - padLeft - padRight;
		const plotH = height - padTop - padBottom;

		const data = getCurveData();
		if (!data || data.points.length === 0) {
			ctx.fillStyle = textColor;
			ctx.font = '14px sans-serif';
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText('暂无曲线数据，点击上方【模拟拧紧】即可生成并监视实时波形', width / 2, height / 2);
			ctx.restore();
			return;
		}

		// Draw background grid
		ctx.strokeStyle = gridColor;
		ctx.lineWidth = 1;
		ctx.setLineDash([4, 4]);

		const xTicks = 6;
		const yTicks = 5;

		// Horizontal grid lines
		for (let i = 0; i <= yTicks; i++) {
			const y = padTop + (plotH / yTicks) * i;
			ctx.beginPath();
			ctx.moveTo(padLeft, y);
			ctx.lineTo(padLeft + plotW, y);
			ctx.stroke();

			// Y axis labels (Torque or Angle)
			ctx.fillStyle = textColor;
			ctx.font = '11px monospace';
			ctx.textAlign = 'right';
			ctx.textBaseline = 'middle';

			if (chartMode === 'angle_time') {
				const val = (data.maxAngle * (1 - i / yTicks)).toFixed(0);
				ctx.fillText(`${val}°`, padLeft - 8, y);
			} else {
				const val = (data.maxTorque * (1 - i / yTicks)).toFixed(1);
				ctx.fillText(`${val}`, padLeft - 8, y);
			}

			// Right Y axis for dual_time (Angle)
			if (chartMode === 'dual_time') {
				ctx.textAlign = 'left';
				const valA = (data.maxAngle * (1 - i / yTicks)).toFixed(0);
				ctx.fillText(`${valA}°`, padLeft + plotW + 8, y);
			}
		}

		// Vertical grid lines
		for (let i = 0; i <= xTicks; i++) {
			const x = padLeft + (plotW / xTicks) * i;
			ctx.beginPath();
			ctx.moveTo(x, padTop);
			ctx.lineTo(x, padTop + plotH);
			ctx.stroke();

			ctx.fillStyle = textColor;
			ctx.font = '11px monospace';
			ctx.textAlign = 'center';
			ctx.textBaseline = 'top';

			if (chartMode === 'torque_angle') {
				const val = ((data.maxAngle / xTicks) * i).toFixed(0);
				ctx.fillText(`${val}°`, x, padTop + plotH + 8);
			} else {
				const val = Math.round((data.totalTimeMs / xTicks) * i);
				ctx.fillText(`${val}ms`, x, padTop + plotH + 8);
			}
		}

		ctx.setLineDash([]); // Reset line dash

		// Axis titles
		ctx.font = '11px sans-serif';
		ctx.fillStyle = textColor;
		ctx.textAlign = 'center';
		if (chartMode === 'torque_angle') {
			ctx.fillText('旋转角度 Angle (°)', padLeft + plotW / 2, height - 10);
		} else {
			ctx.fillText('采样时间 Time (ms)', padLeft + plotW / 2, height - 10);
		}

		ctx.save();
		ctx.translate(14, padTop + plotH / 2);
		ctx.rotate(-Math.PI / 2);
		ctx.fillText(chartMode === 'angle_time' ? '角度 Angle (°)' : '扭矩 Torque (N·m)', 0, 0);
		ctx.restore();

		if (chartMode === 'dual_time') {
			ctx.save();
			ctx.translate(width - 14, padTop + plotH / 2);
			ctx.rotate(Math.PI / 2);
			ctx.fillText('角度 Angle (°)', 0, 0);
			ctx.restore();
		}

		// Coordinate helpers
		const getX = (p: typeof data.points[0]) => {
			if (chartMode === 'torque_angle') {
				return padLeft + (p.angle / data.maxAngle) * plotW;
			}
			return padLeft + (p.timeMs / data.totalTimeMs) * plotW;
		};

		const getYTorque = (val: number) => padTop + (1 - val / data.maxTorque) * plotH;
		const getYAngle = (val: number) => padTop + (1 - val / data.maxAngle) * plotH;

		// 1. Draw Angle Curve
		if (chartMode === 'angle_time' || chartMode === 'dual_time') {
			ctx.beginPath();
			data.points.forEach((p, i) => {
				const x = getX(p);
				const y = getYAngle(p.angle);
				if (i === 0) ctx.moveTo(x, y);
				else ctx.lineTo(x, y);
			});

			if (chartMode === 'angle_time') {
				// Gradient fill
				const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
				grad.addColorStop(0, 'rgba(245, 158, 11, 0.25)');
				grad.addColorStop(1, 'rgba(245, 158, 11, 0.0)');
				ctx.lineTo(padLeft + plotW, padTop + plotH);
				ctx.lineTo(padLeft, padTop + plotH);
				ctx.closePath();
				ctx.fillStyle = grad;
				ctx.fill();
			}

			// Stroke angle line
			ctx.beginPath();
			data.points.forEach((p, i) => {
				const x = getX(p);
				const y = getYAngle(p.angle);
				if (i === 0) ctx.moveTo(x, y);
				else ctx.lineTo(x, y);
			});
			ctx.strokeStyle = '#f59e0b';
			ctx.lineWidth = 2.5;
			ctx.stroke();
		}

		// 2. Draw Torque Curve
		if (chartMode === 'torque_time' || chartMode === 'dual_time' || chartMode === 'torque_angle') {
			ctx.beginPath();
			data.points.forEach((p, i) => {
				const x = getX(p);
				const y = getYTorque(p.torque);
				if (i === 0) ctx.moveTo(x, y);
				else ctx.lineTo(x, y);
			});

			if (chartMode === 'torque_time' || chartMode === 'torque_angle') {
				// Gradient fill
				const grad = ctx.createLinearGradient(0, padTop, 0, padTop + plotH);
				grad.addColorStop(0, 'rgba(6, 182, 212, 0.3)');
				grad.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
				const lastX = getX(data.points[data.points.length - 1]);
				const firstX = getX(data.points[0]);
				ctx.lineTo(lastX, padTop + plotH);
				ctx.lineTo(firstX, padTop + plotH);
				ctx.closePath();
				ctx.fillStyle = grad;
				ctx.fill();
			}

			// Stroke torque line
			ctx.beginPath();
			data.points.forEach((p, i) => {
				const x = getX(p);
				const y = getYTorque(p.torque);
				if (i === 0) ctx.moveTo(x, y);
				else ctx.lineTo(x, y);
			});
			ctx.strokeStyle = '#06b6d4';
			ctx.lineWidth = 2.5;
			ctx.stroke();
		}

		// Highlight Peak Point
		const peakP = data.points[data.peakTIdx];
		if (peakP && (chartMode === 'torque_time' || chartMode === 'dual_time' || chartMode === 'torque_angle')) {
			const px = getX(peakP);
			const py = getYTorque(peakP.torque);
			ctx.beginPath();
			ctx.arc(px, py, 5, 0, Math.PI * 2);
			ctx.fillStyle = '#ef4444';
			ctx.fill();
			ctx.strokeStyle = '#ffffff';
			ctx.lineWidth = 2;
			ctx.stroke();

			ctx.font = 'bold 10px monospace';
			ctx.fillStyle = '#ef4444';
			ctx.textAlign = 'center';
			ctx.fillText(`峰值: ${peakP.torque}N·m`, px, py - 10);
		}

		// Highlight Snug Point
		const snugP = data.points[data.snugIdx];
		if (snugP && (chartMode === 'torque_time' || chartMode === 'dual_time')) {
			const sx = getX(snugP);
			const sy = getYTorque(snugP.torque);
			ctx.beginPath();
			ctx.arc(sx, sy, 4, 0, Math.PI * 2);
			ctx.fillStyle = '#a855f7';
			ctx.fill();
			ctx.strokeStyle = '#ffffff';
			ctx.lineWidth = 1.5;
			ctx.stroke();

			ctx.font = '10px monospace';
			ctx.fillStyle = '#a855f7';
			ctx.textAlign = 'left';
			ctx.fillText(`贴合点: ${snugP.torque}N·m`, sx + 6, sy + 4);
		}

		// Crosshair on hover
		if (hoveredSample) {
			const hx = hoveredSample.x;
			ctx.setLineDash([3, 3]);
			ctx.strokeStyle = isDark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)';
			ctx.lineWidth = 1;
			ctx.beginPath();
			ctx.moveTo(hx, padTop);
			ctx.lineTo(hx, padTop + plotH);
			ctx.stroke();
			ctx.setLineDash([]);

			// Indicator circle on torque
			const ty = getYTorque(hoveredSample.torque);
			ctx.beginPath();
			ctx.arc(hx, ty, 4, 0, Math.PI * 2);
			ctx.fillStyle = '#06b6d4';
			ctx.fill();
			ctx.strokeStyle = '#fff';
			ctx.lineWidth = 1.5;
			ctx.stroke();

			// Indicator circle on angle
			if (chartMode === 'dual_time' || chartMode === 'angle_time') {
				const ay = getYAngle(hoveredSample.angle);
				ctx.beginPath();
				ctx.arc(hx, ay, 4, 0, Math.PI * 2);
				ctx.fillStyle = '#f59e0b';
				ctx.fill();
				ctx.strokeStyle = '#fff';
				ctx.lineWidth = 1.5;
				ctx.stroke();
			}
		}

		ctx.restore();
	}

	function handleMouseMove(e: MouseEvent) {
		if (!canvasElement || !containerElement) return;
		const rect = canvasElement.getBoundingClientRect();
		const mouseX = e.clientX - rect.left;
		const mouseY = e.clientY - rect.top;

		const padLeft = 55;
		const padRight = chartMode === 'dual_time' ? 55 : 25;
		const plotW = rect.width - padLeft - padRight;

		if (mouseX < padLeft || mouseX > padLeft + plotW) {
			hoveredSample = null;
			renderChart();
			return;
		}

		const data = getCurveData();
		if (!data || data.points.length === 0) return;

		let closestIdx = 0;
		if (chartMode === 'torque_angle') {
			const targetAngle = ((mouseX - padLeft) / plotW) * data.maxAngle;
			let minDiff = Infinity;
			data.points.forEach((p, i) => {
				const diff = Math.abs(p.angle - targetAngle);
				if (diff < minDiff) {
					minDiff = diff;
					closestIdx = i;
				}
			});
		} else {
			const ratio = (mouseX - padLeft) / plotW;
			closestIdx = Math.min(
				Math.max(0, Math.round(ratio * (data.points.length - 1))),
				data.points.length - 1
			);
		}

		const sample = data.points[closestIdx];
		const x = chartMode === 'torque_angle'
			? padLeft + (sample.angle / data.maxAngle) * plotW
			: padLeft + (sample.timeMs / data.totalTimeMs) * plotW;

		hoveredSample = {
			index: sample.index,
			timeMs: sample.timeMs,
			torque: sample.torque,
			angle: sample.angle,
			x,
			y: mouseY
		};
		renderChart();
	}

	function handleMouseLeave() {
		hoveredSample = null;
		renderChart();
	}

	async function refreshLatestCurve() {
		try {
			const data = await api.getLatestCurve();
			if (data) {
				setLatestCurves(data);
				showToast({ type: 'success', message: '已同步最新拧紧曲线' });
			} else {
				showToast({ type: 'info', message: '当前尚无已记录的拧紧曲线' });
			}
		} catch {
			showToast({ type: 'error', message: '获取曲线失败' });
		}
	}

	function exportJson() {
		if (!curves) return;
		const jsonStr = JSON.stringify(curves, null, 2);
		const blob = new Blob([jsonStr], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `curve_mid0900_${curves.result_id || 'latest'}_${Date.now()}.json`;
		a.click();
		URL.revokeObjectURL(url);
		showToast({ type: 'success', message: '已导出 MID 0900 JSON 数据' });
	}

	function exportCsv() {
		const data = getCurveData();
		if (!data) return;
		let csv = 'Index,Time_ms,Torque_Nm,Angle_deg\n';
		data.points.forEach((p) => {
			csv += `${p.index},${p.timeMs},${p.torque},${p.angle}\n`;
		});
		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `curve_data_${curves?.result_id || 'latest'}.csv`;
		a.click();
		URL.revokeObjectURL(url);
		showToast({ type: 'success', message: '已导出 CSV 曲线表格' });
	}

	function downloadPng() {
		if (!canvasElement) return;
		const url = canvasElement.toDataURL('image/png');
		const a = document.createElement('a');
		a.href = url;
		a.download = `tightening_trace_${curves?.result_id || 'curve'}.png`;
		a.click();
		showToast({ type: 'success', message: '已保存波形截图 PNG' });
	}
</script>

<div class="card p-5 space-y-4 border border-surface-200-700-token bg-surface-50-900-token rounded-xl shadow-md">
	<!-- Top Bar / Header -->
	<div class="flex flex-wrap items-center justify-between gap-3 border-b border-surface-200-700-token pb-3">
		<div class="flex items-center gap-3">
			<span class="text-2xl">📈</span>
			<div>
				<div class="flex items-center gap-2">
					<h3 class="text-base font-bold text-surface-900 dark:text-surface-100">
						实时拧紧曲线监控 (MID 0900 Trace Curve)
					</h3>
					{#if curves}
						{#if curves.is_ok}
							<span class="px-2 py-0.5 text-xs font-bold rounded-full bg-success-500/20 text-success-500 border border-success-500/40">
								OK 拧紧合格
							</span>
						{:else}
							<span class="px-2 py-0.5 text-xs font-bold rounded-full bg-error-500/20 text-error-500 border border-error-500/40">
								NOK 拧紧超差
							</span>
						{/if}
					{:else}
						<span class="px-2 py-0.5 text-xs font-medium rounded-full bg-surface-300 dark:bg-surface-700 text-surface-600 dark:text-surface-400">
							等待触发
						</span>
					{/if}
				</div>
				<p class="text-xs text-surface-500 dark:text-surface-400">
					Open Protocol 工业现场高频采样 (2ms 物理间隔 / 150 点连续仿真)
				</p>
			</div>
		</div>

		<!-- Action Buttons -->
		<div class="flex items-center gap-2">
			<button
				type="button"
				class="btn btn-sm variant-ghost hover:variant-soft flex items-center gap-1.5 text-xs"
				onclick={refreshLatestCurve}
				title="刷新拉取最新曲线"
			>
				<span>🔄</span>
				<span>同步</span>
			</button>
			<button
				type="button"
				class="btn btn-sm variant-ghost hover:variant-soft flex items-center gap-1.5 text-xs"
				onclick={exportCsv}
				disabled={!curves}
				title="导出 CSV 数据表"
			>
				<span>📄</span>
				<span>CSV</span>
			</button>
			<button
				type="button"
				class="btn btn-sm variant-ghost hover:variant-soft flex items-center gap-1.5 text-xs"
				onclick={exportJson}
				disabled={!curves}
				title="导出原始 MID 0900 JSON"
			>
				<span>💾</span>
				<span>JSON</span>
			</button>
			<button
				type="button"
				class="btn btn-sm variant-ghost hover:variant-soft flex items-center gap-1.5 text-xs"
				onclick={downloadPng}
				disabled={!curves}
				title="保存图表截图"
			>
				<span>📷</span>
				<span>截图</span>
			</button>
		</div>
	</div>

	<!-- Curve Info Pills -->
	{#if curves}
		<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
			<div class="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800 border border-surface-200-700-token">
				<div class="text-surface-500 dark:text-surface-400">终拧扭矩</div>
				<div class="text-sm font-bold font-mono text-cyan-500 mt-0.5">
					{curves.actual_torque.toFixed(2)} N·m
				</div>
			</div>
			<div class="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800 border border-surface-200-700-token">
				<div class="text-surface-500 dark:text-surface-400">终拧角度</div>
				<div class="text-sm font-bold font-mono text-amber-500 mt-0.5">
					{curves.actual_angle.toFixed(1)} °
				</div>
			</div>
			<div class="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800 border border-surface-200-700-token">
				<div class="text-surface-500 dark:text-surface-400">采样点数</div>
				<div class="text-sm font-bold font-mono text-surface-800 dark:text-surface-200 mt-0.5">
					{curves.torque_curve.samples.length} 点
				</div>
			</div>
			<div class="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800 border border-surface-200-700-token">
				<div class="text-surface-500 dark:text-surface-400">采样间隔 / 总长</div>
				<div class="text-sm font-bold font-mono text-surface-800 dark:text-surface-200 mt-0.5">
					{curves.torque_curve.time_interval_ms}ms (300ms)
				</div>
			</div>
			<div class="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800 border border-surface-200-700-token">
				<div class="text-surface-500 dark:text-surface-400">流水号 Result ID</div>
				<div class="text-sm font-bold font-mono text-surface-800 dark:text-surface-200 mt-0.5">
					#{curves.result_id}
				</div>
			</div>
			<div class="p-2.5 rounded-lg bg-surface-100 dark:bg-surface-800 border border-surface-200-700-token truncate">
				<div class="text-surface-500 dark:text-surface-400">采样时间</div>
				<div class="text-xs font-mono text-surface-800 dark:text-surface-200 mt-1 truncate" title={curves.timestamp}>
					{curves.timestamp}
				</div>
			</div>
		</div>
	{/if}

	<!-- View Tabs & Legend -->
	<div class="flex flex-wrap items-center justify-between gap-3 pt-1">
		<div class="inline-flex rounded-lg border border-surface-200-700-token bg-surface-100-800-token p-1">
			<button
				type="button"
				class="px-3 py-1 text-xs font-medium rounded transition-colors"
				class:bg-primary-500={chartMode === 'dual_time'}
				class:text-white={chartMode === 'dual_time'}
				class:opacity-60={chartMode !== 'dual_time'}
				onclick={() => { chartMode = 'dual_time'; renderChart(); }}
			>
				双轴叠加 (Torque & Angle)
			</button>
			<button
				type="button"
				class="px-3 py-1 text-xs font-medium rounded transition-colors"
				class:bg-primary-500={chartMode === 'torque_time'}
				class:text-white={chartMode === 'torque_time'}
				class:opacity-60={chartMode !== 'torque_time'}
				onclick={() => { chartMode = 'torque_time'; renderChart(); }}
			>
				扭矩-时间 (T-t)
			</button>
			<button
				type="button"
				class="px-3 py-1 text-xs font-medium rounded transition-colors"
				class:bg-primary-500={chartMode === 'angle_time'}
				class:text-white={chartMode === 'angle_time'}
				class:opacity-60={chartMode !== 'angle_time'}
				onclick={() => { chartMode = 'angle_time'; renderChart(); }}
			>
				角度-时间 (A-t)
			</button>
			<button
				type="button"
				class="px-3 py-1 text-xs font-medium rounded transition-colors"
				class:bg-primary-500={chartMode === 'torque_angle'}
				class:text-white={chartMode === 'torque_angle'}
				class:opacity-60={chartMode !== 'torque_angle'}
				onclick={() => { chartMode = 'torque_angle'; renderChart(); }}
			>
				扭矩-角度 (T-A 特性图)
			</button>
		</div>

		<!-- Legend -->
		<div class="flex items-center gap-4 text-xs">
			{#if chartMode !== 'angle_time'}
				<div class="flex items-center gap-1.5">
					<span class="inline-block w-3 h-1 rounded bg-cyan-500"></span>
					<span class="text-surface-600 dark:text-surface-300">扭矩 (N·m)</span>
				</div>
			{/if}
			{#if chartMode === 'dual_time' || chartMode === 'angle_time'}
				<div class="flex items-center gap-1.5">
					<span class="inline-block w-3 h-1 rounded bg-amber-500"></span>
					<span class="text-surface-600 dark:text-surface-300">角度 (°)</span>
				</div>
			{/if}
			<div class="flex items-center gap-1.5">
				<span class="inline-block w-2 h-2 rounded-full bg-purple-500"></span>
				<span class="text-surface-600 dark:text-surface-300">贴合点</span>
			</div>
			<div class="flex items-center gap-1.5">
				<span class="inline-block w-2 h-2 rounded-full bg-red-500"></span>
				<span class="text-surface-600 dark:text-surface-300">峰值点</span>
			</div>
		</div>
	</div>

	<!-- Canvas Container -->
	<div
		bind:this={containerElement}
		class="relative w-full h-[340px] rounded-lg bg-surface-900/10 dark:bg-surface-950/40 border border-surface-200-700-token overflow-hidden cursor-crosshair"
	>
		<canvas
			bind:this={canvasElement}
			onmousemove={handleMouseMove}
			onmouseleave={handleMouseLeave}
			class="w-full h-full block"
		></canvas>

		<!-- Floating Tooltip on Hover -->
		{#if hoveredSample}
			<div
				class="absolute pointer-events-none transform -translate-x-1/2 -translate-y-full mb-3 px-2.5 py-1.5 rounded-md bg-surface-900/90 dark:bg-surface-800/90 text-white text-[11px] shadow-lg border border-surface-700 backdrop-blur-sm z-10"
				style="left: {hoveredSample.x}px; top: {Math.max(hoveredSample.y - 10, 45)}px;"
			>
				<div class="font-bold border-b border-surface-700 pb-0.5 mb-1 text-surface-300">
					点 #{hoveredSample.index} ({hoveredSample.timeMs} ms)
				</div>
				<div class="flex items-center justify-between gap-3 text-cyan-400 font-mono">
					<span>扭矩:</span>
					<span>{hoveredSample.torque} N·m</span>
				</div>
				<div class="flex items-center justify-between gap-3 text-amber-400 font-mono">
					<span>角度:</span>
					<span>{hoveredSample.angle}°</span>
				</div>
			</div>
		{/if}
	</div>

	<!-- Bottom Tip / Protocol Info -->
	<div class="flex flex-wrap items-center justify-between text-xs text-surface-500 dark:text-surface-400 pt-1">
		<div>
			💡 提示：在图表上移动鼠标可查看采样点精确数值；支持在上方一键导出标准格式数据包。
		</div>
		<div class="font-mono text-[11px] opacity-70">
			OP Protocol Spec: MID 0900 (Trace Type: 1=Angle, 2=Torque, Res: 16-bit BE)
		</div>
	</div>
</div>
