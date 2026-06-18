'use client'

interface ViewControlsProps {
  onViewChange: (view: 'front' | 'top' | 'side' | 'reset') => void
}

export default function ViewControls({ onViewChange }: ViewControlsProps) {
  return (
    <div className="flex items-center gap-2">
      <button 
        onClick={() => onViewChange('front')}
        className="px-3 py-1.5 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 hover:text-white transition-colors"
        title="前视图 (Y-Z 平面)"
      >
        前视图
      </button>
      <button 
        onClick={() => onViewChange('top')}
        className="px-3 py-1.5 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 hover:text-white transition-colors"
        title="顶视图 (X-Y 平面)"
      >
        顶视图
      </button>
      <button 
        onClick={() => onViewChange('side')}
        className="px-3 py-1.5 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 hover:text-white transition-colors"
        title="侧视图 (X-Z 平面)"
      >
        侧视图
      </button>
      <div className="h-6 w-px bg-gray-700 mx-1"></div>
      <button 
        onClick={() => onViewChange('reset')}
        className="px-3 py-1.5 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 hover:text-white transition-colors"
        title="重置为等轴测视图"
      >
        重置视图
      </button>
    </div>
  )
}
