import * as THREE from 'three'
import { Brush, Evaluator, ADDITION, SUBTRACTION, INTERSECTION } from 'three-bvh-csg'
import { Feature } from '../app/types'

const evaluator = new Evaluator()

function createBrush(geometry: THREE.BufferGeometry): Brush {
  const brush = new Brush(geometry)
  brush.updateMatrix()
  return brush
}

function createBlockGeometry(params: any): THREE.BufferGeometry {
  const { length, width, height } = params
  const geometry = new THREE.BoxGeometry(length, height, width)
  return geometry
}

function createCylinderGeometry(params: any): THREE.BufferGeometry {
  const { diameter, height } = params
  const radius = diameter / 2
  const geometry = new THREE.CylinderGeometry(radius, radius, height, 32)
  return geometry
}

function createConeGeometry(params: any): THREE.BufferGeometry {
  const { base_diameter, top_diameter, height } = params
  const baseRadius = base_diameter / 2
  const topRadius = top_diameter / 2
  const geometry = new THREE.CylinderGeometry(topRadius, baseRadius, height, 32)
  return geometry
}

function createSphereGeometry(params: any): THREE.BufferGeometry {
  const { diameter } = params
  const radius = diameter / 2
  const geometry = new THREE.SphereGeometry(radius, 32, 32)
  return geometry
}

function getFeatureGeometry(feature: Feature): THREE.BufferGeometry | null {
  const pos = feature.position?.calculated_coords || { x: 0, y: 0, z: 0 }
  
  let geometry: THREE.BufferGeometry | null = null
  let centerOffset = { x: 0, y: 0, z: 0 }
  
  if (feature.type === 'block') {
    const { length, width, height } = feature.parameters
    geometry = createBlockGeometry(feature.parameters)
    // NX 块从原点向正方向延伸，需要移到中心点
    centerOffset = {
      x: pos.x + length / 2,
      y: pos.z + height / 2,  // NX Z -> Three Y
      z: pos.y + width / 2   // NX Y -> Three Z
    }
  } else if (feature.type === 'cylinder') {
    const { diameter, height } = feature.parameters
    geometry = createCylinderGeometry(feature.parameters)
    // 圆柱中心在高度的一半处
    centerOffset = {
      x: pos.x,
      y: pos.z + height / 2,  // NX Z -> Three Y
      z: pos.y
    }
  } else if (feature.type === 'cone') {
    const { base_diameter, top_diameter, height } = feature.parameters
    geometry = createConeGeometry(feature.parameters)
    // 圆锥中心在高度的一半处
    centerOffset = {
      x: pos.x,
      y: pos.z + height / 2,
      z: pos.y
    }
  } else if (feature.type === 'sphere') {
    const { diameter } = feature.parameters
    geometry = createSphereGeometry(feature.parameters)
    // 球心在指定位置
    centerOffset = {
      x: pos.x,
      y: pos.z,
      z: pos.y
    }
  }
  
  if (geometry) {
    geometry.translate(centerOffset.x, centerOffset.y, centerOffset.z)
  }
  
  return geometry
}

export function hasBooleanOperations(features: Feature[]): boolean {
  return features.some(f => 
    f.boolean_op === 'subtract' || 
    f.boolean_op === 'unite' || 
    f.boolean_op === 'intersect'
  )
}

export function performCSGOperations(features: Feature[]): THREE.BufferGeometry | null {
  if (features.length === 0) return null
  
  try {
    let result: Brush | null = null
    
    for (let i = 0; i < features.length; i++) {
      const feature = features[i]
      const geometry = getFeatureGeometry(feature)
      
      if (!geometry) continue
      
      const brush = createBrush(geometry)
      
      if (i === 0) {
        result = brush
      } else {
        if (!result) continue
        
        if (feature.boolean_op === 'subtract') {
          result = evaluator.evaluate(result, brush, SUBTRACTION) as Brush
        } else if (feature.boolean_op === 'unite') {
          result = evaluator.evaluate(result, brush, ADDITION) as Brush
        } else if (feature.boolean_op === 'intersect') {
          result = evaluator.evaluate(result, brush, INTERSECTION) as Brush
        }
      }
    }
    
    if (result) {
      result.geometry.computeVertexNormals()
      return result.geometry
    }
    
    return null
  } catch (error) {
    console.error('CSG operations failed:', error)
    return null
  }
}
