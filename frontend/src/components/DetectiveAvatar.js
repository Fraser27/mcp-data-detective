import React from 'react';

function DetectiveAvatar({ className = "h-8 w-8" }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 64 64" 
      className={className}
      fill="currentColor"
    >
      <path d="M32 2C15.432 2 2 15.432 2 32s13.432 30 30 30 30-13.432 30-30S48.568 2 32 2zm0 5c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm-9 7c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm18 0c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm-9 2c7.732 0 14 6.268 14 14s-6.268 14-14 14-14-6.268-14-14 6.268-14 14-14zm-16 5c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm32 0c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm-16 1c-4.418 0-8 3.582-8 8s3.582 8 8 8 8-3.582 8-8-3.582-8-8-8zm0 2c3.314 0 6 2.686 6 6s-2.686 6-6 6-6-2.686-6-6 2.686-6 6-6zm-21 8c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm42 0c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm-21 8c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm-9 7c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2zm18 0c1.105 0 2 .895 2 2s-.895 2-2 2-2-.895-2-2 .895-2 2-2z"/>
      <path d="M32 16c-1.105 0-2 .895-2 2v2c0 1.105.895 2 2 2s2-.895 2-2v-2c0-1.105-.895-2-2-2z"/>
      <path d="M32 24c-1.105 0-2 .895-2 2v2c0 1.105.895 2 2 2s2-.895 2-2v-2c0-1.105-.895-2-2-2z"/>
      <path d="M24 32c-1.105 0-2 .895-2 2s.895 2 2 2h16c1.105 0 2-.895 2-2s-.895-2-2-2H24z"/>
      <path d="M32 40c-1.105 0-2 .895-2 2v2c0 1.105.895 2 2 2s2-.895 2-2v-2c0-1.105-.895-2-2-2z"/>
      <path d="M32 48c-1.105 0-2 .895-2 2v2c0 1.105.895 2 2 2s2-.895 2-2v-2c0-1.105-.895-2-2-2z"/>
    </svg>
  );
}

export default DetectiveAvatar;