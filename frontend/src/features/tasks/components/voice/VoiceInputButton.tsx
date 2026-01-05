// SPDX-FileCopyrightText: 2025 Weibo, Inc.
//
// SPDX-License-Identifier: Apache-2.0

'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIsMobile } from '@/features/layout/hooks/useMediaQuery';
import { useTranslation } from '@/hooks/useTranslation';
import { useToast } from '@/hooks/use-toast';
import VoiceWaveform from './VoiceWaveform';

interface VoiceInputButtonProps {
  onTranscriptComplete: (text: string) => void;
  disabled?: boolean;
}

/**
 * VoiceInputButton Component
 *
 * Provides voice input functionality with long-press to record:
 * - Desktop: Long-press Mic button to record, release to send
 * - Mobile: Tap Mic to expand to long bar, long-press to record
 *
 * Features:
 * - Real-time waveform visualization
 * - 120-second max recording duration
 * - Multi-language support (auto-detect: Chinese/English)
 * - Live transcript preview
 */
export default function VoiceInputButton({
  onTranscriptComplete,
  disabled = false,
}: VoiceInputButtonProps) {
  const { t } = useTranslation('chat');
  const { toast } = useToast();
  const isMobile = useIsMobile();

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);

  // Audio context and analyzer for waveform
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Refs for long-press detection
  const isPressingRef = useRef(false);
  const hasStartedRecordingRef = useRef(false);

  // Max recording duration (120 seconds)
  const MAX_RECORDING_DURATION = 120;
  // Long-press threshold (500ms)
  const LONG_PRESS_THRESHOLD = 500;

  /**
   * Initialize audio context and analyzer for waveform visualization
   */
  const initializeAudioContext = useCallback(async () => {
    try {
      // Create AudioContext with lower latency for better responsiveness
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass({ latencyHint: 'interactive' });
      audioContextRef.current = audioContext;

      // Get user media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
        },
      });
      mediaStreamRef.current = stream;

      // Create analyser for waveform visualization
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256; // Balance between detail and performance
      analyserRef.current = analyser;

      // Connect stream to analyser
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyser);

      return stream;
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
      toast({
        title: t('voice.microphone_access_denied'),
        description: t('voice.microphone_access_denied_desc'),
        variant: 'destructive',
      });
      throw error;
    }
  }, [t, toast]);

  /**
   * Start recording
   */
  const startRecording = useCallback(async () => {
    if (disabled || isRecording) return;

    try {
      const stream = await initializeAudioContext();

      // Create MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Start recording
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      hasStartedRecordingRef.current = true;
      setRecordingDuration(0);

      // Start duration timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((prev) => {
          if (prev >= MAX_RECORDING_DURATION) {
            stopRecording();
            return MAX_RECORDING_DURATION;
          }
          return prev + 1;
        });
      }, 1000);

      // Start waveform animation
      const animateWaveform = () => {
        if (!isRecording || !analyserRef.current) return;
        animationFrameRef.current = requestAnimationFrame(animateWaveform);
      };
      animateWaveform();

    } catch (error) {
      console.error('Failed to start recording:', error);
      setIsRecording(false);
      hasStartedRecordingRef.current = false;
    }
  }, [disabled, isRecording, initializeAudioContext]);

  /**
   * Stop recording and transcribe
   */
  const stopRecording = useCallback(async () => {
    if (!isRecording) return;

    setIsRecording(false);
    hasStartedRecordingRef.current = false;

    // Clear timers
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Stop MediaRecorder
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    // Stop audio stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
    }

    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      await audioContextRef.current.close();
    }

    // Check if we have audio data
    if (audioChunksRef.current.length === 0) {
      return;
    }

    // Process audio
    setIsProcessing(true);

    try {
      // Create audio blob
      const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm';
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

      // Transcribe audio
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');

      const response = await fetch('/api/voice/recognize', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const result = await response.json();

      if (result.text) {
        onTranscriptComplete(result.text);
      } else {
        toast({
          title: t('voice.no_speech_detected'),
          description: t('voice.no_speech_detected_desc'),
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Transcription error:', error);
      toast({
        title: t('voice.transcription_failed'),
        description: t('voice.transcription_failed_desc'),
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  }, [isRecording, onTranscriptComplete, t, toast]);

  /**
   * Handle mouse/touch down (start long-press detection)
   */
  const handlePointerDown = useCallback(() => {
    if (disabled || isRecording || isProcessing) return;

    isPressingRef.current = false;
    hasStartedRecordingRef.current = false;

    // Start long-press timer
    longPressTimerRef.current = setTimeout(() => {
      isPressingRef.current = true;
      startRecording();
    }, LONG_PRESS_THRESHOLD);
  }, [disabled, isRecording, isProcessing, startRecording]);

  /**
   * Handle mouse/touch up (end long-press or send)
   */
  const handlePointerUp = useCallback(async () => {
    // Clear long-press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // If we were recording, stop and transcribe
    if (isRecording) {
      await stopRecording();
      return;
    }

    // If not recording and not pressing, it's a tap (toggle expanded mode on mobile)
    if (!isPressingRef.current && !hasStartedRecordingRef.current && isMobile) {
      setIsExpanded(!isExpanded);
    }
  }, [isRecording, isMobile, isExpanded, stopRecording]);

  /**
   * Handle pointer leave (cancel long-press)
   */
  const handlePointerLeave = useCallback(() => {
    // Clear long-press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // If we were recording, stop and transcribe
    if (isRecording) {
      stopRecording();
    }

    isPressingRef.current = false;
  }, [isRecording, stopRecording]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Clear all timers
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      // Stop media stream
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }

      // Close audio context
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []);

  /**
   * Render expanded mobile UI (long bar with Mic and Send buttons)
   */
  if (isExpanded && isMobile) {
    return (
      <div className="flex items-center gap-2">
        {/* Mic button - long press to record */}
        <Button
          type="button"
          variant={isRecording ? 'destructive' : 'ghost'}
          size="icon"
          className={isRecording ? 'animate-pulse' : ''}
          disabled={disabled || isProcessing}
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerLeave}
          onTouchStart={(e) => {
            e.preventDefault();
            handlePointerDown();
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            handlePointerUp();
          }}
        >
          {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
        </Button>

        {/* Waveform visualization */}
        {isRecording && analyserRef.current && (
          <div className="flex-1 flex items-center justify-center">
            <VoiceWaveform
              analyser={analyserRef.current}
              isRecording={isRecording}
              duration={recordingDuration}
              maxDuration={MAX_RECORDING_DURATION}
            />
          </div>
        )}

        {/* Send/Close button */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => setIsExpanded(false)}
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
    );
  }

  /**
   * Render normal UI (single Mic button)
   */
  return (
    <Button
      type="button"
      variant={isRecording ? 'destructive' : 'ghost'}
      size="icon"
      className={isRecording ? 'animate-pulse' : ''}
      disabled={disabled || isProcessing}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerLeave}
      onTouchStart={(e) => {
        e.preventDefault();
        handlePointerDown();
      }}
      onTouchEnd={(e) => {
        e.preventDefault();
        handlePointerUp();
      }}
    >
      {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
    </Button>
  );
}
