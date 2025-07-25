import React from 'react';

function SherlockAvatar({ className = "h-8 w-8" }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 64 64" 
      className={className}
      fill="currentColor"
    >
      {/* Sherlock Holmes silhouette with pipe and hat */}
      <path d="M32 4c-5.523 0-10 4.477-10 10v2c0 2.21.895 4.21 2.344 5.656L26 23.312V26h-6c-3.314 0-6 2.686-6 6v4c0 1.105.895 2 2 2h4v14c0 4.418 3.582 8 8 8h8c4.418 0 8-3.582 8-8V38h4c1.105 0 2-.895 2-2v-4c0-3.314-2.686-6-6-6h-6v-2.688l1.656-1.656C41.105 20.21 42 18.21 42 16v-2c0-5.523-4.477-10-10-10zm0 4c3.314 0 6 2.686 6 6v2c0 1.105-.448 2.105-1.172 2.828L34 21.656V28h-4v-6.344l-2.828-2.828C26.448 18.105 26 17.105 26 16v-2c0-3.314 2.686-6 6-6z"/>
      {/* Deerstalker hat */}
      <path d="M32 2c-6.627 0-12 5.373-12 12 0 1.657.336 3.235.945 4.672L18 22v4h2l2-2h20l2 2h2v-4l-2.945-3.328C43.664 17.235 44 15.657 44 14c0-6.627-5.373-12-12-12zm0 4c4.418 0 8 3.582 8 8 0 1.105-.224 2.158-.625 3.125L38 20H26l-1.375-2.875C24.224 16.158 24 15.105 24 14c0-4.418 3.582-8 8-8z"/>
      {/* Pipe */}
      <path d="M20 36c-1.105 0-2 .895-2 2s.895 2 2 2h4c1.105 0 2-.895 2-2s-.895-2-2-2h-4z"/>
      <path d="M18 38c0-1.105-.895-2-2-2h-4c-1.105 0-2 .895-2 2s.895 2 2 2h4c1.105 0 2-.895 2-2z"/>
      <path d="M12 36c-1.105 0-2 .895-2 2s.895 2 2 2 2-.895 2-2-.895-2-2-2z"/>
    </svg>
  );
}

export default SherlockAvatar;