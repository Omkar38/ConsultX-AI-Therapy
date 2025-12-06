import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useEffect, useRef, useState } from 'react'
import { AudioLines, MessageCircleMore, Mic, MicOff, PhoneOff, Video, VideoOff, Webcam  } from 'lucide-react'
import ChatLayout from '@/features/chat/ChatLayout'

export const Route = createFileRoute('/chat-new')({
  // component: VideoChatPage,
  component: ChatLayout,
})

// // User's floating camera view component
// interface UserCameraViewProps {
//   isCameraOff: boolean
//   videoRef: React.RefObject<HTMLVideoElement | null>
// }

// const UserCameraView = ({ isCameraOff, videoRef }: UserCameraViewProps) => {
//   return (
//     <div className="absolute bottom-6 right-6 w-48 h-36 bg-white rounded-xl overflow-hidden border-2 border-white shadow-lg z-10">
//       {isCameraOff ? (
//         <div className="w-full h-full bg-[#E3E2F0] flex items-center justify-center">
//           <Webcam />
//         </div>
//       ) : (
//         <video
//           ref={videoRef}
//           className="w-full h-full object-cover"
//           playsInline
//           muted
//           aria-label="Your camera view"
//         />
//       )}
//     </div>
//   )
// }

// // Main avatar display component
// const AvatarDisplay = () => {
//   const [isListening, setIsListening] = useState(false)
//   const [isSpeaking, setIsSpeaking] = useState(false)

//   // Simulate conversation states (need to tweak with real data later)
//   useEffect(() => {
//     const interval = setInterval(() => {
//       setIsListening((prev) => !prev)
//       setTimeout(() => {
//         setIsSpeaking((prev) => !prev)
//       }, 2000)
//     }, 8000)

//     return () => clearInterval(interval)
//   }, [])

//   return (
//     <div className="flex-1 flex flex-col items-center justify-center p-8">
//       {/* Avatar Circle */}
//       <div className="relative mb-8">
//         <div
//           className={`w-48 h-48 rounded-full flex items-center justify-center transition-all duration-1000 ${
//             isListening
//               ? 'bg-linear-to-br from-[#70A8A2] to-[#4A90A0] scale-105'
//               : isSpeaking
//                 ? 'bg-linear-to-br from-[#6879A1] to-[#4A90A0] scale-110'
//                 : 'bg-linear-to-br from-[#4A90A0] to-[#6879A1]'
//           }`}
//         >
//           {isListening ? <AudioLines size={100} strokeWidth={1.5} color="#ffffff"/> : <MessageCircleMore size={100} strokeWidth={1.5} color="#ffffff" />}
//         </div>
        
//         {/* Listening/Speaking indicator rings */}
//         {(isListening || isSpeaking) && (
//           <div className="absolute inset-0 rounded-full">
//             <div
//               className={`absolute inset-0 rounded-full border-2 animate-ping ${
//                 isListening ? 'border-[#70A8A2]' : 'border-[#6879A1]'
//               }`}
//               style={{ animationDuration: '2s' }}
//             />
//             {/* <div
//               className={`absolute inset-2 rounded-full border border-opacity-30 animate-pulse ${
//                 isListening ? 'border-[#70A8A2]' : 'border-[#6879A1]'
//               }`}
//             /> */}
//           </div>
//         )}
//       </div>

//       {/* Status Text */}
//       <div className="text-center max-w-md">
//         <h2 className="text-xl font-medium text-gray-800 mb-2">
//           {isListening
//             ? 'Listening...'
//             : isSpeaking
//               ? 'Speaking...'
//               : 'Ready to help'}
//         </h2>
//         <p className="text-base text-gray-600 leading-relaxed">
//           {isListening
//             ? 'I\'m here to listen to whatever is on your mind today.'
//             : isSpeaking
//               ? 'Let me share some thoughts on what you\'ve said.'
//               : 'Your wellness companion is ready when you are.'}
//         </p>
//       </div>
//     </div>
//   )
// }

// // Control buttons component
// interface ControlButtonsProps {
//   isMuted: boolean
//   isCameraOff: boolean
//   onToggleMute: () => void
//   onToggleCamera: () => void
//   onEndSession: () => void
// }

// const ControlButtons = ({
//   isMuted,
//   isCameraOff,
//   onToggleMute,
//   onToggleCamera,
//   onEndSession,
// }: ControlButtonsProps) => {
//   return (
//     <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-4 bg-white/90 backdrop-blur-sm rounded-2xl px-6 py-3 shadow-lg">
//       {/* Mute Button */}
//       <button
//         onClick={onToggleMute}
//         className={`p-3 rounded-xl transition-all duration-200 ${
//           isMuted
//             ? 'bg-[#C46262] text-white'
//             : 'bg-[#F6F4F2] text-[#4A90A0] hover:bg-[#4A90A0] hover:text-white'
//         }`}
//         aria-label={isMuted ? 'Unmute' : 'Mute'}
//       >

//         {isMuted ? <MicOff size={20} /> : <Mic size={20} />}
//       </button>

//       {/* Camera Button */}
//       <button
//         onClick={onToggleCamera}
//         className={`p-3 rounded-xl transition-all duration-200 ${
//           isCameraOff
//             ? 'bg-[#C46262] text-white'
//             : 'bg-[#F6F4F2] text-[#4A90A0] hover:bg-[#4A90A0] hover:text-white'
//         }`}
//         aria-label={isCameraOff ? 'Turn camera on' : 'Turn camera off'}
//       >
//         {isCameraOff ? <VideoOff size={20} /> : <Video size={20} />}
//       </button>

//       {/* End Session Button */}
//       <button
//         onClick={onEndSession}
//         className="p-3 rounded-xl bg-[#C46262] text-white hover:bg-red-600 transition-all duration-200"
//         aria-label="End session"
//       >
//         <PhoneOff size={20} />
//       </button>
//     </div>
//   )
// }

// // Session header component
// interface SessionHeaderProps {
//   isConnected: boolean
// }

// const SessionHeader = ({ isConnected }: SessionHeaderProps) => {
//   const [sessionTime, setSessionTime] = useState(0)

//   useEffect(() => {
//     if (!isConnected) return

//     const interval = setInterval(() => {
//       setSessionTime((prev) => prev + 1)
//     }, 1000)

//     return () => clearInterval(interval)
//   }, [isConnected])

//   const formatTime = (seconds: number) => {
//     const mins = Math.floor(seconds / 60)
//     const secs = seconds % 60
//     return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
//   }

//   return (
//     <div className="absolute top-6 left-6 right-6 flex items-center justify-between z-10">
//       <div className="bg-white/90 backdrop-blur-sm rounded-xl px-4 py-2 shadow-sm">
//         <h1 className="text-lg font-medium text-gray-900">Wellness Session</h1>
//         <p className="text-sm text-gray-600">
//           {isConnected ? 'Connected' : 'Session ended'}
//         </p>
//       </div>
      
//       <div className="bg-white/90 backdrop-blur-sm rounded-xl px-4 py-2 shadow-sm flex items-center gap-2">
//         <div
//           className={`w-2 h-2 rounded-full ${
//             isConnected ? 'bg-[#6BAF7A]' : 'bg-gray-400'
//           }`}
//         />
//         <span className="text-sm font-medium text-gray-700">
//           {isConnected ? formatTime(sessionTime) : 'Disconnected'}
//         </span>
//       </div>
//     </div>
//   )
// }

// // Main video chat page component
// function VideoChatPage() {
//   const [isMuted, setIsMuted] = useState(false)
//   const [isCameraOff, setCameraOff] = useState(false)
//   const [isConnected, setIsConnected] = useState(true)

//   const videoRef = useRef<HTMLVideoElement | null>(null)
//   const streamRef = useRef<MediaStream | null>(null)

//   const navigate = useNavigate()

//   const handleEndSession = () => {
//     setIsConnected(false)
//     // Stop camera stream
//     if (streamRef.current) {
//       streamRef.current.getTracks().forEach((track) => track.stop())
//       streamRef.current = null
//     }
//     console.log('Session ended');
    
//     // Navigate to feedback page
//     setTimeout(() => {
//       navigate({ to: '/feedback' })
//     }, 1000)
//   }

//   const toggleMute = () => setIsMuted(!isMuted)
//   const toggleCamera = () => setCameraOff(!isCameraOff)

//   // Camera management
//   useEffect(() => {
//     let mounted = true

//     const startCamera = async () => {
//       if (isCameraOff || !isConnected) {
//         // Stop existing stream
//         if (streamRef.current) {
//           streamRef.current.getTracks().forEach((track) => track.stop())
//           streamRef.current = null
//         }
//         return
//       }

//       try {
//         const stream = await navigator.mediaDevices.getUserMedia({
//           video: { width: 320, height: 240 },
//           audio: false,
//         })
        
//         if (!mounted) {
//           stream.getTracks().forEach((track) => track.stop())
//           return
//         }
        
//         streamRef.current = stream
//         if (videoRef.current) {
//           videoRef.current.srcObject = stream
//           videoRef.current.play().catch(() => {})
//         }
//       } catch (error) {
//         console.log('Unable to access camera:', error)
//       }
//     }

//     startCamera()

//     return () => {
//       mounted = false
//       if (streamRef.current) {
//         streamRef.current.getTracks().forEach((track) => track.stop())
//         streamRef.current = null
//       }
//     }
//   }, [isCameraOff, isConnected])

//   return (
//     <div className="h-screen w-screen bg-linear-to-br from-[#D8EFE8] to-[#E3E2F0] overflow-hidden">
//       {/* Session Header */}
//       <SessionHeader isConnected={isConnected} />
      
//       {/* Main Avatar Area */}
//       <div className="h-full w-full relative flex">
//         <AvatarDisplay />
        
//         {/* User Camera View - Floating */}
//         {isConnected && (
//           <UserCameraView isCameraOff={isCameraOff} videoRef={videoRef} />
//         )}
        
//         {/* Control Buttons */}
//         {isConnected && (
//           <ControlButtons
//             isMuted={isMuted}
//             isCameraOff={isCameraOff}
//             onToggleMute={toggleMute}
//             onToggleCamera={toggleCamera}
//             onEndSession={handleEndSession}
//           />
//         )}
//       </div>
//     </div>
//   )
// }
