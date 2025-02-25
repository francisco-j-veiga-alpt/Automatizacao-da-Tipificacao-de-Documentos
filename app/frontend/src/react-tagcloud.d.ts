// src/react-tagcloud.d.ts
declare module 'react-tagcloud' {
  import * as React from 'react';

  export interface TagCloudTag {
    value: string;
    count: number;
  }

  export interface TagCloudProps {
    tags: TagCloudTag[];
    className?: string;
    style?: React.CSSProperties;
    minSize?: number;
    maxSize?: number;
    shuffle?: boolean;
    onClick?: (tag: TagCloudTag) => void;
    callbacks?: {
      onTagClicked?: (tag: TagCloudTag) => void;
      getWordColor?: (tag: TagCloudTag) => string;
      getWordTooltip?: (tag: TagCloudTag) => string;
    };
  }

  export class TagCloud extends React.Component<TagCloudProps> {}
}
