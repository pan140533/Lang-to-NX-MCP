'use client'

import { Canvas, useThree } from '@react-three/fiber'
import { OrbitControls, Grid, PerspectiveCamera } from '@react-three/drei'
import { Feature } from '../types'
import { useEffect, useRef, useMemo, useState } from 'react'
import * as THREE from 'three'
import { performCSGOperations, hasBooleanOperations } from '../../lib/csgOperations'

interface ThreeViewerProps {
  features: Feature[]
  viewCommand?: 'front' | 'top' | 'side' | 'reset' | null
  onViewChanged?: () => void
  selectedFeatureId?: string | null
  onFeatureSelect?: (featureId: string | null) => void
}

// 块组件
// 坐标系转换：NX (X, Y, Z) → Three.js (X, Z, Y)
// NX: X(右), Y(前), Z(上)
// Three.js: X(右), Y(上), Z(前)
function Block({ length, width, height, position, featureId, isSelected, isHovered, onSelect, onHover }: any) {
  // NX 坐标转 Three.js 坐标
  const threePos = {
    x: position.x,
    y: position.z,  // NX 的 Z(上) → Three.js 的 Y(上)
    z: position.y   // NX 的 Y(前) → Three.js 的 Z(前)
  }
  
  // NX 尺寸转 Three.js 尺寸
  const threeSize = {
    x: length,      // X 方向不变
    y: height,      // NX 的 height(Z方向) → Three.js 的 Y 方向
    z: width        // NX 的 width(Y方向) → Three.js 的 Z 方向
  }
  
  // 根据状态确定颜色
  const getColor = () => {
    if (isSelected) return '#ffd700'  // 金色 - 选中
    if (isHovered) return '#60a5fa'   // 浅蓝色 - 悬停
    return '#4a9eff'                   // 默认蓝色
  }
  
  return (
    <mesh 
      position={[
        threePos.x + threeSize.x / 2,
        threePos.y + threeSize.y / 2,
        threePos.z + threeSize.z / 2
      ]}
      onClick={(e) => {
        e.stopPropagation()
        if (onSelect) onSelect(featureId)
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        if (onHover) onHover(featureId)
      }}
      onPointerOut={(e) => {
        e.stopPropagation()
        if (onHover) onHover(null)
      }}
    >
      <boxGeometry args={[threeSize.x, threeSize.y, threeSize.z]} />
      <meshStandardMaterial 
        color={getColor()} 
        transparent={isHovered && !isSelected}
        opacity={isHovered && !isSelected ? 0.8 : 1}
      />
    </mesh>
  )
}

// 圆柱组件
// 坐标系转换：NX (X, Y, Z) → Three.js (X, Z, Y)
// NX 圆柱沿 Z 轴向上，Three.js CylinderGeometry 默认沿 Y 轴向上
function Cylinder({ diameter, height, position, featureId, isSelected, isHovered, onSelect, onHover }: any) {
  const radius = diameter / 2
  
  // NX 坐标转 Three.js 坐标
  const threePos = {
    x: position.x,
    y: position.z,  // NX 的 Z(上) → Three.js 的 Y(上)
    z: position.y   // NX 的 Y(前) → Three.js 的 Z(前)
  }
  
  // 根据状态确定颜色
  const getColor = () => {
    if (isSelected) return '#ffd700'  // 金色 - 选中
    if (isHovered) return '#f87171'   // 浅红色 - 悬停
    return '#ff6b6b'                   // 默认红色
  }
  
  // 圆柱在 Three.js 中默认沿 Y 轴，正好对应 NX 的 Z 轴，不需要旋转！
  return (
    <mesh 
      position={[
        threePos.x,
        threePos.y + height / 2,  // 圆柱中心在高度的一半处
        threePos.z
      ]}
      onClick={(e) => {
        e.stopPropagation()
        if (onSelect) onSelect(featureId)
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        if (onHover) onHover(featureId)
      }}
      onPointerOut={(e) => {
        e.stopPropagation()
        if (onHover) onHover(null)
      }}
    >
      <cylinderGeometry args={[radius, radius, height, 32]} />
      <meshStandardMaterial 
        color={getColor()}
        transparent={isHovered && !isSelected}
        opacity={isHovered && !isSelected ? 0.8 : 1}
      />
    </mesh>
  )
}

// 圆锥组件
// 坐标系转换：NX (X, Y, Z) → Three.js (X, Z, Y)
// NX 圆锥沿 Z 轴向上，Three.js CylinderGeometry 默认沿 Y 轴向上
function Cone({ base_diameter, top_diameter, height, position, featureId, isSelected, isHovered, onSelect, onHover }: any) {
  const baseRadius = base_diameter / 2
  const topRadius = top_diameter / 2
  
  // NX 坐标转 Three.js 坐标
  const threePos = {
    x: position.x,
    y: position.z,  // NX 的 Z(上) → Three.js 的 Y(上)
    z: position.y   // NX 的 Y(前) → Three.js 的 Z(前)
  }
  
  // 根据状态确定颜色
  const getColor = () => {
    if (isSelected) return '#ffd700'  // 金色 - 选中
    if (isHovered) return '#fb923c'   // 浅橙色 - 悬停
    return '#ffa500'                   // 默认橙色
  }
  
  // Three.js CylinderGeometry 参数：(radiusTop, radiusBottom, height, radialSegments)
  return (
    <mesh 
      position={[
        threePos.x,
        threePos.y + height / 2,  // 圆锥中心在高度的一半处
        threePos.z
      ]}
      onClick={(e) => {
        e.stopPropagation()
        if (onSelect) onSelect(featureId)
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        if (onHover) onHover(featureId)
      }}
      onPointerOut={(e) => {
        e.stopPropagation()
        if (onHover) onHover(null)
      }}
    >
      <cylinderGeometry args={[topRadius, baseRadius, height, 32]} />
      <meshStandardMaterial 
        color={getColor()}
        transparent={isHovered && !isSelected}
        opacity={isHovered && !isSelected ? 0.8 : 1}
      />
    </mesh>
  )
}

// 球组件
// 坐标系转换：NX (X, Y, Z) → Three.js (X, Z, Y)
function Sphere({ diameter, position, featureId, isSelected, isHovered, onSelect, onHover }: any) {
  const radius = diameter / 2
  
  // NX 坐标转 Three.js 坐标
  const threePos = {
    x: position.x,
    y: position.z,  // NX 的 Z(上) → Three.js 的 Y(上)
    z: position.y   // NX 的 Y(前) → Three.js 的 Z(前)
  }
  
  // 根据状态确定颜色
  const getColor = () => {
    if (isSelected) return '#ffd700'  // 金色 - 选中
    if (isHovered) return '#c084fc'   // 浅紫色 - 悬停
    return '#9b59b6'                   // 默认紫色
  }
  
  return (
    <mesh 
      position={[
        threePos.x,
        threePos.y,  // 球心在指定位置
        threePos.z
      ]}
      onClick={(e) => {
        e.stopPropagation()
        if (onSelect) onSelect(featureId)
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        if (onHover) onHover(featureId)
      }}
      onPointerOut={(e) => {
        e.stopPropagation()
        if (onHover) onHover(null)
      }}
    >
      <sphereGeometry args={[radius, 32, 32]} />
      <meshStandardMaterial 
        color={getColor()}
        transparent={isHovered && !isSelected}
        opacity={isHovered && !isSelected ? 0.8 : 1}
      />
    </mesh>
  )
}

// 相机控制器
function CameraController({ viewCommand, onViewChanged, focusTarget, features }: { viewCommand?: string | null, onViewChanged?: () => void, focusTarget?: { x: number, y: number, z: number } | null, features?: Feature[] }) {
  const { camera } = useThree()
  const controlsRef = useRef<any>()
  const initialPositionSet = useRef(false)

  useEffect(() => {
    if (!initialPositionSet.current && features && features.length > 0) {
      camera.position.set(400, 400, 400)
      camera.lookAt(0, 0, 0)
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0)
        controlsRef.current.update()
      }
      initialPositionSet.current = true
    }
  }, [features, camera])

  useEffect(() => {
    if (!viewCommand && !focusTarget) return
    if (!controlsRef.current) return

    let newPosition: THREE.Vector3
    let targetPosition: THREE.Vector3

    if (focusTarget) {
      return
    } else if (viewCommand) {
      const distance = 500
      switch (viewCommand) {
        case 'front':
          newPosition = new THREE.Vector3(distance, 0, 0)
          break
        case 'top':
          newPosition = new THREE.Vector3(0, 0, distance)
          break
        case 'side':
          newPosition = new THREE.Vector3(0, distance, 0)
          break
        case 'reset':
          newPosition = new THREE.Vector3(400, 400, 400)
          break
        default:
          return
      }
      targetPosition = new THREE.Vector3(0, 0, 0)
    } else {
      return
    }

    camera.position.copy(newPosition)
    camera.lookAt(targetPosition)
    controlsRef.current.target.copy(targetPosition)
    controlsRef.current.update()
    
    if (onViewChanged) {
      onViewChanged()
    }
  }, [viewCommand, camera, onViewChanged, focusTarget])

  return (
    <OrbitControls 
      ref={controlsRef}
      enableDamping
      dampingFactor={0.05}
      minDistance={100}
      maxDistance={2000}
    />
  )
}

// CSG 结果组件
function CSGResult({ features, selectedFeatureId, onFeatureSelect }: { features: Feature[], selectedFeatureId?: string | null, onFeatureSelect?: (id: string | null) => void }) {
  // 使用 useMemo 缓存 CSG 计算结果
  const { geometry: csgGeometry, error } = useMemo(() => {
    if (features.length === 0) return { geometry: null, error: null }
    
    console.log('[CSG] 开始计算，features:', JSON.stringify(features.map(f => ({
      type: f.type,
      boolean_op: f.boolean_op,
      params: f.parameters,
      pos: f.position?.calculated_coords
    }))))
    
    try {
      const result = performCSGOperations(features)
      console.log('[CSG] 计算结果:', result ? '成功' : '失败')
      return { geometry: result, error: result ? null : new Error('CSG returned null') }
    } catch (error) {
      console.error('[CSG] 计算失败:', error)
      return { geometry: null, error }
    }
  }, [features])
  
  // 检查是否选中了特定特征
  const isSpecificSelected = selectedFeatureId !== null && features.some(f => f.feature_id === selectedFeatureId)
  
  // CSG 失败时回退到原始渲染
  if (error || !csgGeometry) {
    console.log('[CSG] 回退到原始渲染')
    return (
      <group>
        {features.map((feature, index) => {
          const pos = feature.position?.calculated_coords || { x: 0, y: 0, z: 0 }
          const isSelected = selectedFeatureId === feature.feature_id
          
          if (feature.type === 'block') {
            return (
              <Block
                key={feature.feature_id}
                featureId={feature.feature_id}
                length={feature.parameters.length}
                width={feature.parameters.width}
                height={feature.parameters.height}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={() => {}}
              />
            )
          } else if (feature.type === 'cylinder') {
            return (
              <Cylinder
                key={feature.feature_id}
                featureId={feature.feature_id}
                diameter={feature.parameters.diameter}
                height={feature.parameters.height}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={() => {}}
              />
            )
          } else if (feature.type === 'cone') {
            return (
              <Cone
                key={feature.feature_id}
                featureId={feature.feature_id}
                base_diameter={feature.parameters.base_diameter}
                top_diameter={feature.parameters.top_diameter}
                height={feature.parameters.height}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={() => {}}
              />
            )
          } else if (feature.type === 'sphere') {
            return (
              <Sphere
                key={feature.feature_id}
                featureId={feature.feature_id}
                diameter={feature.parameters.diameter}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={() => {}}
              />
            )
          }
          return null
        })}
      </group>
    )
  }
  
  // CSG 成功时只渲染结果，不渲染原始特征
  return (
    <group>
      <mesh geometry={csgGeometry}>
        <meshStandardMaterial 
          color="#4a9eff" 
          side={THREE.DoubleSide}
          flatShading={false}
        />
      </mesh>
    </group>
  )
}

// 场景内容
function Scene({ features, viewCommand, onViewChanged, selectedFeatureId, onFeatureSelect }: ThreeViewerProps) {
  // 检查是否有布尔运算
  const hasBoolean = hasBooleanOperations(features)
  
  // 计算选中特征的焦点位置（暂时禁用，因为导致问题）
  const focusTarget = null
  
  // 处理悬停和选中回调
  const handleHover = (featureId: string | null) => {
    // 暂时不在这里处理，使用外部传入的
  }
  
  // 点击空白处取消选择
  const handleBackgroundClick = (e: any) => {
    if (e.object.name === 'background') {
      if (onFeatureSelect) onFeatureSelect(null)
    }
  }
  
  return (
    <>
      {/* 相机 */}
      <PerspectiveCamera makeDefault position={[400, 400, 400]} fov={50} />
      
      {/* 轨道控制器 */}
      <CameraController viewCommand={viewCommand} onViewChanged={onViewChanged} focusTarget={focusTarget} features={features} />
      
      {/* 光照 */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
      <directionalLight position={[-10, -10, -5]} intensity={0.3} />
      
      {/* 网格地面 */}
      <Grid 
        args={[1000, 1000]} 
        cellSize={50} 
        cellThickness={0.5}
        cellColor="#6b7280"
        sectionSize={100}
        sectionThickness={1}
        sectionColor="#9ca3af"
        fadeDistance={1500}
        fadeStrength={1}
        followCamera={false}
        infiniteGrid={true}
      />
      
      {/* 点击背景取消选择 */}
      <mesh 
        position={[0, -1, 0]} 
        rotation={[-Math.PI / 2, 0, 0]} 
        name="background"
        onClick={(e) => {
          e.stopPropagation()
          if (onFeatureSelect) onFeatureSelect(null)
        }}
      >
        <planeGeometry args={[10000, 10000]} />
        <meshBasicMaterial visible={false} />
      </mesh>
      
      {/* 渲染特征 */}
      {hasBoolean ? (
        // 如果有布尔运算，使用 CSG 渲染
        <CSGResult features={features} selectedFeatureId={selectedFeatureId} onFeatureSelect={onFeatureSelect} />
      ) : (
        // 否则使用原有的独立渲染方式
        features.map((feature, index) => {
          const pos = feature.position?.calculated_coords || { x: 0, y: 0, z: 0 }
          const isSelected = selectedFeatureId === feature.feature_id
          
          if (feature.type === 'block') {
            return (
              <Block
                key={feature.feature_id}
                featureId={feature.feature_id}
                length={feature.parameters.length}
                width={feature.parameters.width}
                height={feature.parameters.height}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={handleHover}
              />
            )
          } else if (feature.type === 'cylinder') {
            return (
              <Cylinder
                key={feature.feature_id}
                featureId={feature.feature_id}
                diameter={feature.parameters.diameter}
                height={feature.parameters.height}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={handleHover}
              />
            )
          } else if (feature.type === 'cone') {
            return (
              <Cone
                key={feature.feature_id}
                featureId={feature.feature_id}
                base_diameter={feature.parameters.base_diameter}
                top_diameter={feature.parameters.top_diameter}
                height={feature.parameters.height}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={handleHover}
              />
            )
          } else if (feature.type === 'sphere') {
            return (
              <Sphere
                key={feature.feature_id}
                featureId={feature.feature_id}
                diameter={feature.parameters.diameter}
                position={pos}
                isSelected={isSelected}
                isHovered={false}
                onSelect={onFeatureSelect}
                onHover={handleHover}
              />
            )
          }
          return null
        })
      )}
    </>
  )
}

export default function ThreeViewer({ features, viewCommand, onViewChanged, selectedFeatureId, onFeatureSelect }: ThreeViewerProps) {
  return (
    <Canvas
      shadows
      gl={{ antialias: true }}
      style={{ background: 'linear-gradient(to bottom right, #111827, #1a1d23, #111827)' }}
    >
      <Scene 
        features={features} 
        viewCommand={viewCommand} 
        onViewChanged={onViewChanged}
        selectedFeatureId={selectedFeatureId}
        onFeatureSelect={onFeatureSelect}
      />
    </Canvas>
  )
}
