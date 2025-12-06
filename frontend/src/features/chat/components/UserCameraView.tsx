import React, { useEffect, useRef, useState } from 'react'
import { Webcam } from 'lucide-react'

// User's floating camera view component
interface UserCameraViewProps {
  isCameraOff: boolean
  videoRef: React.RefObject<HTMLVideoElement | null>
}

const UserCameraView = ({ isCameraOff, videoRef }: UserCameraViewProps) => {
  return (
    <div className="absolute bottom-6 left-6 w-48 h-36 bg-white rounded-xl overflow-hidden border-2 border-white shadow-lg z-10">
      {isCameraOff ? (
        <div className="w-full h-full bg-[#E3E2F0] flex items-center justify-center">
          <Webcam />
        </div>
      ) : (
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          playsInline
          muted
          aria-label="Your camera view"
        />
      )}
    </div>
  )
}

export default UserCameraView;