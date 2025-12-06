import { Mic, MicOff, PhoneOff, Video, VideoOff } from 'lucide-react'

// Control buttons component
interface ControlButtonsProps {
  // isMuted: boolean
  isCameraOff: boolean
  // onToggleMute: () => void
  onToggleCamera: () => void
  onEndSession: () => void
  isListening: boolean
  onToggleSpeechRecognition: () => void
}

const ControlButtons = ({
  // isMuted,
  isCameraOff,
  // onToggleMute,
  onToggleCamera,
  onEndSession,
  isListening,
  onToggleSpeechRecognition

}: ControlButtonsProps) => {
  return (
    <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-4 bg-white/90 backdrop-blur-sm rounded-2xl px-6 py-3 shadow-lg">
      {/* Mute Button */}
      <button
        onClick={onToggleSpeechRecognition}
        className={`p-3 rounded-xl transition-all duration-200 ${
          isListening
            ? 'bg-[#F6F4F2] text-[#4A90A0] hover:bg-[#4A90A0] hover:text-white'
            : 'bg-[#C46262] text-white'
        }`}
        aria-label={isListening ? 'Unmute' : 'Mute'}
      >

        {isListening ? <Mic size={20} /> : <MicOff size={20} />}
      </button>

      {/* Camera Button */}
      <button
        onClick={onToggleCamera}
        className={`p-3 rounded-xl transition-all duration-200 ${
          isCameraOff
            ? 'bg-[#C46262] text-white'
            : 'bg-[#F6F4F2] text-[#4A90A0] hover:bg-[#4A90A0] hover:text-white'
        }`}
        aria-label={isCameraOff ? 'Turn camera on' : 'Turn camera off'}
      >
        {isCameraOff ? <VideoOff size={20} /> : <Video size={20} />}
      </button>

      {/* End Session Button */}
      <button
        onClick={onEndSession}
        className="p-3 rounded-xl bg-[#C46262] text-white hover:bg-red-600 transition-all duration-200"
        aria-label="End session"
      >
        <PhoneOff size={20} />
      </button>
    </div>
  )
}

export default ControlButtons;