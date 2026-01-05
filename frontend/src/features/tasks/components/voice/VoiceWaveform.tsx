// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import React, { useEffect, useRef } from 'react';

interface VoiceWaveformProps {
  analyser: AnalyserNode;
  isRecording: boolean;
  duration: number;
  maxDuration: number;
}

/**
 * VoiceWaveform Component
 *
 * Visualizes audio input as a waveform animation
 * Shows real-time audio volume levels
 */
export default function VoiceWaveform({
  analyser,
  isRecording,
  duration,
  maxDuration,
}: VoiceWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !analyser) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    /**
     * Draw waveform
     */
    const draw = () => {
      if (!isRecording) {
        animationRef.current = null;
        return;
      }

      animationRef.current = requestAnimationFrame(draw);

      // Get frequency data
      analyser.getByteFrequencyData(dataArray);

      // Clear canvas
      ctx.clearRect(0, 0, rect.width, rect.height);

      // Calculate average volume
      const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength;

      // Draw waveform bars
      const barCount = 30; // Number of bars
      const barWidth = rect.width / barCount;
      const gap = 2;
      const maxHeight = rect.height * 0.8; // Max height is 80% of canvas

      ctx.fillStyle = '#14B8A6'; // Teal primary color

      for (let i = 0; i < barCount; i++) {
        // Use frequency data to determine bar height
        const dataIndex = Math.floor((i / barCount) * bufferLength);
        const value = dataArray[dataIndex] / 255; // Normalize to 0-1

        // Add some randomness for visual interest
        const height = (value * maxHeight * 0.5) + (Math.random() * maxHeight * 0.2);
        const x = i * barWidth;
        const y = (rect.height - height) / 2;

        // Draw rounded bar
        const radius = Math.min(barWidth - gap, height) / 2;
        ctx.beginPath();
        ctx.roundRect(x + gap / 2, y, barWidth - gap, height, radius);
        ctx.fill();
      }

      // Draw duration text
      const timeText = `${Math.floor(duration)}s / ${maxDuration}s`;
      ctx.fillStyle = '#666666';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(timeText, rect.width / 2, rect.height - 5);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [analyser, isRecording, duration, maxDuration]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full h-16 bg-surface rounded-lg"
      style={{ display: 'block' }}
    />
  );
}
