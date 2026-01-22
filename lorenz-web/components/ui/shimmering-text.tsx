'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { motion, useInView } from 'motion/react';

interface ShimmeringTextProps extends React.HTMLAttributes<HTMLSpanElement> {
  text: string;
  duration?: number;
  delay?: number;
  repeat?: boolean;
  repeatDelay?: number;
  startOnView?: boolean;
  once?: boolean;
  spread?: number;
  color?: string;
  shimmerColor?: string;
}

const ShimmeringText = React.forwardRef<HTMLSpanElement, ShimmeringTextProps>(
  (
    {
      text,
      duration = 2,
      delay = 0,
      repeat = true,
      repeatDelay = 0.5,
      startOnView = true,
      once = false,
      spread = 2,
      color,
      shimmerColor,
      className,
      ...props
    },
    ref
  ) => {
    const spanRef = React.useRef<HTMLSpanElement>(null);
    const isInView = useInView(spanRef, {
      once,
    });

    const shouldAnimate = startOnView ? isInView : true;

    const shimmerGradient = React.useMemo(() => {
      const baseColor = color || 'currentColor';
      const highlightColor = shimmerColor || 'hsl(252 85% 78%)';

      return `linear-gradient(
        90deg,
        ${baseColor} 0%,
        ${baseColor} 40%,
        ${highlightColor} 50%,
        ${baseColor} 60%,
        ${baseColor} 100%
      )`;
    }, [color, shimmerColor]);

    return (
      <span
        ref={(node) => {
          // @ts-ignore
          spanRef.current = node;
          if (typeof ref === 'function') ref(node);
          else if (ref) ref.current = node;
        }}
        className={cn('inline-block', className)}
        {...props}
      >
        <motion.span
          style={{
            backgroundImage: shimmerGradient,
            backgroundSize: `${100 * spread}% 100%`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
          initial={{ backgroundPosition: '100% 0%' }}
          animate={
            shouldAnimate
              ? {
                  backgroundPosition: ['100% 0%', '-100% 0%'],
                }
              : { backgroundPosition: '100% 0%' }
          }
          transition={{
            duration,
            delay,
            repeat: repeat ? Infinity : 0,
            repeatDelay,
            ease: 'linear',
          }}
        >
          {text}
        </motion.span>
      </span>
    );
  }
);
ShimmeringText.displayName = 'ShimmeringText';

export { ShimmeringText };
