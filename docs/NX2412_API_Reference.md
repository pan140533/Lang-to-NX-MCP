# NX 2412 API Reference
> Extracted from C++ headers

## ExtrudeBuilder
File: `Features_ExtrudeBuilder.hxx`

```cpp
    namespace Features
    {
        class ExtrudeBuilder;
    }
    class Direction;
    namespace Features
    {
        class FeatureBuilder;
    }
    namespace GeometricUtilities
    {
        class BooleanOperation;
    }
    namespace GeometricUtilities
        class FeatureOptions;
    }
    namespace GeometricUtilities
    {
        class Limits;
    }
    namespace GeometricUtilities
    namespace GeometricUtilities
    {
        class SmartVolumeProfileBuilder;
    }
    class Section;
    /** This enum represents the type of limit */
    enum ExtrudeLimitDataLimitType
            Following are default values and options.
             <br>
             <br>
            <b> Section </b> Must be set by user
             <br>
             <br>
             <br>
            <b> Section </b> Must be set by user
             <br>
             <br>
            <b> Direction </b> Must be set by user
             <br>
             <br>
             <br>
            <b> Boolean Target </b>  NULL
             <br>
             <br>
            <b> Allow Self-intersecting Section </b> false
             <br>
          <br> To create a new instance of this class, use @link NXOpen::Features::FeatureCollection::CreateExtrudeBuilder  NXOpen::Features::FeatureCollection::CreateExtrudeBuilder @endlink  <br>
             <br>
             <br>
            <b> Allow Self-intersecting Section </b> false
             <br>
          <br> To create a new instance of this class, use @link NXOpen::Features::FeatureCollection::CreateExtrudeBuilder  NXOpen::Features::FeatureCollection::CreateExtrudeBuilder @endlink  <br>
        Default values.
        <list type="table">
            /**Returns  the section
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Section * Section
            (
            );
            /**Sets  the section
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetSection
            (
                NXOpen::Section * section /** Section to be extruded This parameter may not be NULL.*/
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetSection
            (
                NXOpen::Section * section /** Section to be extruded This parameter may not be NULL.*/
            );
            /**Returns  the extrude direction
            /**Returns  the extrude direction
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Direction * Direction
            (
            );
            /**Sets  the extrude direction
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetDirection
            (
                NXOpen::Direction * direction /** Extrude direction This parameter may not be NULL.*/
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetDirection
            (
                NXOpen::Direction * direction /** Extrude direction This parameter may not be NULL.*/
            );
            /**Returns  the distance tolerance
            /**Returns  the extrude boolean operation
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::GeometricUtilities::BooleanOperation * BooleanOperation
            (
            );
            /**Returns  the extrude limits
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::GeometricUtilities::Limits * Limits
            (
            );
            /** SET option for supporting self-intersecting section
             <br>  Created in NX7.5.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void AllowSelfIntersectingSection
            (
                bool allowSelfIntersectingSection /** If true, allow self-intersecting section. */
             <br>  Created in NX7.5.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void AllowSelfIntersectingSection
            (
                bool allowSelfIntersectingSection /** If true, allow self-intersecting section. */
            );
        };
```

## ChamferBuilder
File: `Features_ChamferBuilder.hxx`

```cpp
        /** Represents the chamfer builder data.
            <br> To create a new instance of this class, use @link NXOpen::Features::FeatureCollection::CreateChamferBuilder  NXOpen::Features::FeatureCollection::CreateChamferBuilder @endlink  <br>
         <br>  Created in NX4.0.0.  <br>
        */
            /** This enum represents the chamfer parameter options */
            public: enum ChamferOption
            {
                ChamferOptionSymmetricOffsets/** Symmetric offsets */,
                ChamferOptionTwoOffsets/** Two offset distances */,
                ChamferOptionOffsetAndAngle/** Offset distance and angle */
                ChamferOptionSymmetricOffsets/** Symmetric offsets */,
                ChamferOptionTwoOffsets/** Two offset distances */,
                ChamferOptionOffsetAndAngle/** Offset distance and angle */
            };
                ChamferOptionTwoOffsets/** Two offset distances */,
                ChamferOptionOffsetAndAngle/** Offset distance and angle */
            };
            /** This enum represents the offset method options */
            public: enum OffsetMethod
            {
                OffsetMethodEdgesAlongFaces/** Offset edges along faces */,
            /** This enum represents the offset method options */
            public: enum OffsetMethod
            {
                OffsetMethodEdgesAlongFaces/** Offset edges along faces */,
                OffsetMethodFacesAndTrim/** Offset faces and trim */
            };
                OffsetMethodEdgesAlongFaces/** Offset edges along faces */,
                OffsetMethodFacesAndTrim/** Offset faces and trim */
            };
            /**Sets  the offset reverse status
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetReverseOffsets
            (
                bool reverse /** reverse */
            /**Sets  the chamfer parameter option.
                     <br>
                       @link Features::ChamferBuilder::ChamferOptionSymmetricOffsets Features::ChamferBuilder::ChamferOptionSymmetricOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionTwoOffsets Features::ChamferBuilder::ChamferOptionTwoOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionOffsetAndAngle Features::ChamferBuilder::ChamferOptionOffsetAndAngle@endlink
            /**Sets  the chamfer parameter option.
                     <br>
                       @link Features::ChamferBuilder::ChamferOptionSymmetricOffsets Features::ChamferBuilder::ChamferOptionSymmetricOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionTwoOffsets Features::ChamferBuilder::ChamferOptionTwoOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionOffsetAndAngle Features::ChamferBuilder::ChamferOptionOffsetAndAngle@endlink
                     <br>
            /**Sets  the chamfer parameter option.
                     <br>
                       @link Features::ChamferBuilder::ChamferOptionSymmetricOffsets Features::ChamferBuilder::ChamferOptionSymmetricOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionTwoOffsets Features::ChamferBuilder::ChamferOptionTwoOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionOffsetAndAngle Features::ChamferBuilder::ChamferOptionOffsetAndAngle@endlink
                     <br>
                    Each of these options correspond to a chamfer defined by two equal
            /**Sets   the offset method. <br>
                       @link Features::ChamferBuilder::OffsetMethodEdgesAlongFaces Features::ChamferBuilder::OffsetMethodEdgesAlongFaces@endlink
                       @link Features::ChamferBuilder::OffsetMethodFacesAndTrim Features::ChamferBuilder::OffsetMethodFacesAndTrim@endlink
                        <br>
            /**Sets   the offset method. <br>
                       @link Features::ChamferBuilder::OffsetMethodEdgesAlongFaces Features::ChamferBuilder::OffsetMethodEdgesAlongFaces@endlink
                       @link Features::ChamferBuilder::OffsetMethodFacesAndTrim Features::ChamferBuilder::OffsetMethodFacesAndTrim@endlink
                        <br>
                    The EdgesAlongFaces method is the normal chamfer in which the chamfer
            /**Sets   the offset method. <br>
                       @link Features::ChamferBuilder::OffsetMethodEdgesAlongFaces Features::ChamferBuilder::OffsetMethodEdgesAlongFaces@endlink
                       @link Features::ChamferBuilder::OffsetMethodFacesAndTrim Features::ChamferBuilder::OffsetMethodFacesAndTrim@endlink
                        <br>
                    The EdgesAlongFaces method is the normal chamfer in which the chamfer
                    boundary is determined by offsetting the input edges along its adjacent
                    faces. The FacesAndTrim method is the free-form chamfer in which the
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetMethod
            (
                NXOpen::Features::ChamferBuilder::OffsetMethod method /** method */
            );
            /**Sets  the first offset distance (expression). Please do not use this property to access/modify
            /**Sets  the first offset distance (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::FirstOffsetExp Features::ChamferBuilder::FirstOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::FirstOffsetExp Features::ChamferBuilder::FirstOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetFirstOffset
            (
                const NXString & offsetExpression /** offset expression */
            /**Sets  the first offset distance (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::FirstOffsetExp Features::ChamferBuilder::FirstOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::FirstOffsetExp Features::ChamferBuilder::FirstOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            void SetFirstOffset
            (
                const char * offsetExpression /** offset expression */
            /**Sets  the second offset distance (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::SecondOffsetExp Features::ChamferBuilder::SecondOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::SecondOffsetExp Features::ChamferBuilder::SecondOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetSecondOffset
            (
                const NXString & offsetExpression /** offset expression */
            /**Sets  the second offset distance (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::SecondOffsetExp Features::ChamferBuilder::SecondOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::SecondOffsetExp Features::ChamferBuilder::SecondOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            void SetSecondOffset
            (
                const char * offsetExpression /** offset expression */
            /**Sets  the chamfer angle (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::AngleExp Features::ChamferBuilder::AngleExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::AngleExp Features::ChamferBuilder::AngleExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetAngle
            (
                const NXString & angleExpression /** angle expression */
            /**Sets  the chamfer angle (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::AngleExp Features::ChamferBuilder::AngleExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::AngleExp Features::ChamferBuilder::AngleExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            void SetAngle
            (
                const char * angleExpression /** angle expression */
            /**Returns  the offset reverse status
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: bool ReverseOffsets
            (
            );
            /**Returns  the chamfer parameter option.
                     <br>
                       @link Features::ChamferBuilder::ChamferOptionSymmetricOffsets Features::ChamferBuilder::ChamferOptionSymmetricOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionTwoOffsets Features::ChamferBuilder::ChamferOptionTwoOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionOffsetAndAngle Features::ChamferBuilder::ChamferOptionOffsetAndAngle@endlink
            /**Returns  the chamfer parameter option.
                     <br>
                       @link Features::ChamferBuilder::ChamferOptionSymmetricOffsets Features::ChamferBuilder::ChamferOptionSymmetricOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionTwoOffsets Features::ChamferBuilder::ChamferOptionTwoOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionOffsetAndAngle Features::ChamferBuilder::ChamferOptionOffsetAndAngle@endlink
                     <br>
            /**Returns  the chamfer parameter option.
                     <br>
                       @link Features::ChamferBuilder::ChamferOptionSymmetricOffsets Features::ChamferBuilder::ChamferOptionSymmetricOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionTwoOffsets Features::ChamferBuilder::ChamferOptionTwoOffsets@endlink
                       @link Features::ChamferBuilder::ChamferOptionOffsetAndAngle Features::ChamferBuilder::ChamferOptionOffsetAndAngle@endlink
                     <br>
                    Each of these options correspond to a chamfer defined by two equal
            /**Returns   the offset method. <br>
                       @link Features::ChamferBuilder::OffsetMethodEdgesAlongFaces Features::ChamferBuilder::OffsetMethodEdgesAlongFaces@endlink
                       @link Features::ChamferBuilder::OffsetMethodFacesAndTrim Features::ChamferBuilder::OffsetMethodFacesAndTrim@endlink
                        <br>
            /**Returns   the offset method. <br>
                       @link Features::ChamferBuilder::OffsetMethodEdgesAlongFaces Features::ChamferBuilder::OffsetMethodEdgesAlongFaces@endlink
                       @link Features::ChamferBuilder::OffsetMethodFacesAndTrim Features::ChamferBuilder::OffsetMethodFacesAndTrim@endlink
                        <br>
                    The EdgesAlongFaces method is the normal chamfer in which the chamfer
            /**Returns   the offset method. <br>
                       @link Features::ChamferBuilder::OffsetMethodEdgesAlongFaces Features::ChamferBuilder::OffsetMethodEdgesAlongFaces@endlink
                       @link Features::ChamferBuilder::OffsetMethodFacesAndTrim Features::ChamferBuilder::OffsetMethodFacesAndTrim@endlink
                        <br>
                    The EdgesAlongFaces method is the normal chamfer in which the chamfer
                    boundary is determined by offsetting the input edges along its adjacent
                    faces. The FacesAndTrim method is the free-form chamfer in which the
                    input edges, using the chamfer parameters in either case.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Features::ChamferBuilder::OffsetMethod Method
            (
            );
            /**Returns  the first offset distance (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::FirstOffsetExp Features::ChamferBuilder::FirstOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::FirstOffsetExp Features::ChamferBuilder::FirstOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXString FirstOffset
            (
            );
            /**Returns  the first offset expression object of chamfer.
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: NXOpen::Expression * FirstOffsetExp
            (
            );
            /**Returns  the second offset distance (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::SecondOffsetExp Features::ChamferBuilder::SecondOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::SecondOffsetExp Features::ChamferBuilder::SecondOffsetExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXString SecondOffset
            (
            );
            /**Returns  the second offset expression object of chamfer.
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: NXOpen::Expression * SecondOffsetExp
            (
            );
            /**Returns  the chamfer angle (expression). Please do not use this property to access/modify
                the @link Features::ChamferBuilder::AngleExp Features::ChamferBuilder::AngleExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
                the @link Features::ChamferBuilder::AngleExp Features::ChamferBuilder::AngleExp@endlink .
                This might be removed from KF bindings in NX 9.
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXString Angle
            (
            );
            /**Returns  the angle expression object of chamfer.
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: NXOpen::Expression * AngleExp
            (
            );
```

## EdgeBlendBuilder
File: `Features_EdgeBlendBuilder.hxx`

```cpp
        /** Represents a Edge Blend builder.
             <br> To create a new instance of this class, use @link NXOpen::Features::FeatureCollection::CreateEdgeBlendBuilder  NXOpen::Features::FeatureCollection::CreateEdgeBlendBuilder @endlink  <br>
        Default values.
        <list type="table">
            /** Get all the variable radii data for an edge in the edge blend  @return  Parameter locations of points on the edge
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::GetVariableRadiusDataNew Features::EdgeBlendBuilder::GetVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::GetVariableRadiusDataNew Features::EdgeBlendBuilder::GetVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NX_DEPRECATED("Deprecated in NX6.0.0.  Use Features::EdgeBlendBuilder::GetVariableRadiusDataNew instead.") std::vector<double> GetVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to get all the varible radius data on*/,
            /** Get all the variable radii data for an edge in the edge blend
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : None */
            public: void GetVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to get all the varible radius data on*/,
            /** Add an edge blend variable radius data for an edge in the edge blend  @return  Index of where variable radius data item is created
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::AddVariableRadiusDataNew Features::EdgeBlendBuilder::AddVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::AddVariableRadiusDataNew Features::EdgeBlendBuilder::AddVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: NX_DEPRECATED("Deprecated in NX6.0.0.  Use Features::EdgeBlendBuilder::AddVariableRadiusDataNew instead.") int AddVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Add an edge blend variable radius data for an edge in the edge blend  @return  Index of where variable radius data item is created
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::AddVariableRadiusDataNew Features::EdgeBlendBuilder::AddVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::AddVariableRadiusDataNew Features::EdgeBlendBuilder::AddVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            int AddVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Add an edge blend variable radius data for an edge in the edge blend
                  * Note: This ja will always create arclength parameter  @return  Index of where variable radius data item is created
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: int AddVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Add an edge blend variable radius data for an edge in the edge blend
                  * Note: This ja will always create arclength parameter  @return  Index of where variable radius data item is created
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            int AddVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Add an edge blend variable radius data for an edge in the edge blend  @return  Index of where variable radius data item is created
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: int AddVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Add an edge blend variable radius data for an edge in the edge blend  @return  Index of where variable radius data item is created
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            int AddVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Edit an edge blend variable radius data for an edge in the edge blend
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::EditVariableRadiusDataNew Features::EdgeBlendBuilder::EditVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::EditVariableRadiusDataNew Features::EdgeBlendBuilder::EditVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: NX_DEPRECATED("Deprecated in NX6.0.0.  Use Features::EdgeBlendBuilder::EditVariableRadiusDataNew instead.") void EditVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Edit an edge blend variable radius data for an edge in the edge blend
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::EditVariableRadiusDataNew Features::EdgeBlendBuilder::EditVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX6.0.0.  Use @link Features::EdgeBlendBuilder::EditVariableRadiusDataNew Features::EdgeBlendBuilder::EditVariableRadiusDataNew@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            void EditVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Edit an edge blend variable radius data for an edge in the edge blend
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void EditVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Edit an edge blend variable radius data for an edge in the edge blend
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            void EditVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Edit an edge blend variable radius data for an edge in the edge blend
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void EditVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Edit an edge blend variable radius data for an edge in the edge blend
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            void EditVariableRadiusDataNew
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Remove variable radius data on an edge by the parameter value of the point on the edge
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void RemoveVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to add stop short data on*/,
            /** Remove variable radius data on an edge by the index into the point array on the edge
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void RemoveVariableRadiusDataByIndex
            (
                NXOpen::Edge * edge /** Edge to remove variable radius data on*/,
            /** Remove all variable radius datas on an edge
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void RemoveVariableRadiusData
            (
                NXOpen::Edge * edge /** Edge to remove all variable radius datas from*/
            /**Returns  the forced cliff edges for edge blend
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::ScCollector * CliffEdges
            (
            );
            /**Sets  the forced cliff edges for edge blend
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetCliffEdges
            (
                NXOpen::ScCollector * cliffEdgeCollector /**The cliff edge collector */
            /**Returns  the prohibited cliff edges for edge blend
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::ScCollector * NonCliffEdges
            (
            );
            /**Sets  the prohibited cliff edges for edge blend
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetNonCliffEdges
            (
                NXOpen::ScCollector * nonCliffEdgeCollector /**The non cliff edge collector */
            /**Returns  the zero slope radius function at chain ends option
             <br>  Created in NX10.0.1.  <br>
             <br> License requirements : None */
            public: bool ZeroSlopeRadiusFunctionAtChainEnds
            (
            );
            /**Sets  the zero slope radius function at chain ends option
             <br>  Created in NX10.0.1.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetZeroSlopeRadiusFunctionAtChainEnds
            (
                bool optionValue /** optionvalue */
            /** Get circular section variable radius point expression for an edge blend for the given list of edges  @return   The primary expression of this variable radius point
             <br>  Created in NX2406.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Expression * GetCircularVariableRadiusExpression
            (
                const std::vector<NXOpen::Edge *> & edgeArray /** Array of edges that are used by the edge chain */,
            /** Get conic variable radius point expressions for an edge blend for the given list of edges
             <br>  Created in NX2406.0.0.  <br>
             <br> License requirements : None */
            public: void GetConicVariableRadiusExpressions
            (
                const std::vector<NXOpen::Edge *> & edgeArray /** Array of edges that are used by the edge chain */,
            /** Get variable radius point parameter expression for an edge blend for the given list of edges  @return   The parameter expression of variable radius point location
             <br>  Created in NX2406.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Expression * GetVariableRadiusParameterExpression
            (
                const std::vector<NXOpen::Edge *> & edgeArray /** Array of edges that are used by the edge chain */,
```

## RevolveBuilder
File: `Features_RevolveBuilder.hxx`

```cpp
        class FeatureBuilder;
    }
    namespace GeometricUtilities
    {
        class BooleanOperation;
    }
    namespace GeometricUtilities
        class FeatureOptions;
    }
    namespace GeometricUtilities
    {
        class Limits;
    }
    namespace GeometricUtilities
    namespace GeometricUtilities
    {
        class SmartVolumeProfileBuilder;
    }
    class Section;
    namespace Features
    {
        /** Represents a revolve builder.
             <br> To create a new instance of this class, use @link NXOpen::Features::FeatureCollection::CreateRevolveBuilder  NXOpen::Features::FeatureCollection::CreateRevolveBuilder @endlink  <br>
        Default values.
        <list type="table">
            /**Sets  the section
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetSection
            (
                NXOpen::Section * section /** This parameter may not be NULL.*/
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetSection
            (
                NXOpen::Section * section /** This parameter may not be NULL.*/
            );
            /**Returns  the section
            /**Returns  the section
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : None */
            public: NXOpen::Section * Section
            (
            );
            /**Returns  the revolve boolean
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : None */
            public: NXOpen::GeometricUtilities::BooleanOperation * BooleanOperation
            (
            );
            /**Returns  the limit data
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : None */
            public: NXOpen::GeometricUtilities::Limits * Limits
            (
            );
```

## BooleanBuilder
File: `Features_BooleanBuilder.hxx`

```cpp
            /**Returns  the boolean operation
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Features::Feature::BooleanType Operation
            (
            );
            /**Returns  the target body
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::Body * Target
            (
            );
            /**Returns  the tool body
             <br>  @deprecated Deprecated in NX5.0.2.  Use @link Features::BooleanBuilder::ToolBodyCollector Features::BooleanBuilder::ToolBodyCollector@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX5.0.2.  Use @link Features::BooleanBuilder::ToolBodyCollector Features::BooleanBuilder::ToolBodyCollector@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NX_DEPRECATED("Deprecated in NX5.0.2.  Use Features::BooleanBuilder::ToolBodyCollector instead.") NXOpen::DisplayableObject * Tool
            (
            );
            /**Returns  the retain target flag
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: bool RetainTarget
            (
            );
            /**Sets  the boolean operation
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetOperation
            (
                NXOpen::Features::Feature::BooleanType operation /** Type of boolean operation. */
            /**Sets  the target body
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetTarget
            (
                NXOpen::Body * target /** Target body for boolean operation. This parameter may not be NULL.*/
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetTarget
            (
                NXOpen::Body * target /** Target body for boolean operation. This parameter may not be NULL.*/
            );
            /**Sets  the tool body
            /**Sets  the tool body
             <br>  @deprecated Deprecated in NX5.0.2.  Use @link Features::BooleanBuilder::SetToolBodyCollector Features::BooleanBuilder::SetToolBodyCollector@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br>  @deprecated Deprecated in NX5.0.2.  Use @link Features::BooleanBuilder::SetToolBodyCollector Features::BooleanBuilder::SetToolBodyCollector@endlink  instead. <br>
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: NX_DEPRECATED("Deprecated in NX5.0.2.  Use Features::BooleanBuilder::SetToolBodyCollector instead.") void SetTool
            (
                NXOpen::DisplayableObject * tool /** Tool body for boolean operation. This parameter may not be NULL.*/
            /**Sets  the retain target flag
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetRetainTarget
            (
                bool retainTarget /** Retain target flag */
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetRetainTarget
            (
                bool retainTarget /** Retain target flag */
            );
            /**Sets  the retain tool flag
            /**Returns  the target bodies for the boolean operation
             <br>  @deprecated Deprecated in NX2312.0.0.  Use @link Features::BooleanBuilder::TargetBodyCollector Features::BooleanBuilder::TargetBodyCollector@endlink  instead. <br>
             <br>  Created in NX5.0.0.  <br>
             <br>  @deprecated Deprecated in NX2312.0.0.  Use @link Features::BooleanBuilder::TargetBodyCollector Features::BooleanBuilder::TargetBodyCollector@endlink  instead. <br>
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : None */
            public: NX_DEPRECATED("Deprecated in NX2312.0.0.  Use Features::BooleanBuilder::TargetBodyCollector instead.") NXOpen::SelectBodyList * Targets
            (
            );
            /**Returns  the tool bodies for the boolean operation for versions before 7.5 but tool body collector for newer versions
             <br>  @deprecated Deprecated in NX7.5.0.  Use @link Features::BooleanBuilder::ToolBodyCollector Features::BooleanBuilder::ToolBodyCollector@endlink  instead. <br>
             <br>  Created in NX5.0.0.  <br>
             <br>  @deprecated Deprecated in NX7.5.0.  Use @link Features::BooleanBuilder::ToolBodyCollector Features::BooleanBuilder::ToolBodyCollector@endlink  instead. <br>
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : None */
            public: NX_DEPRECATED("Deprecated in NX7.5.0.  Use Features::BooleanBuilder::ToolBodyCollector instead.") NXOpen::SelectDisplayableObjectList * Tools
            (
            );
            /**Returns  the tool body collector for the boolean operation
             <br>  Created in NX7.5.0.  <br>
             <br> License requirements : None */
            public: NXOpen::ScCollector * ToolBodyCollector
            (
            );
            /**Sets  the tool body collector for the boolean operation
             <br>  Created in NX7.5.0.  <br>
             <br> License requirements : None */
            public: void SetToolBodyCollector
            (
                NXOpen::ScCollector * toolBodyCollector /** toolbodycollector */
            /**Returns  the tool body collector for the boolean operation
             <br>  Created in NX1847.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::ScCollector * ToolBodyCollector1
            (
            );
            /**Sets  the tool body collector for the boolean operation
             <br>  Created in NX1847.0.0.  <br>
             <br> License requirements : None */
            public: void SetToolBodyCollector1
            (
                NXOpen::ScCollector * toolBodyCollector /** toolbodycollector */
            /**Returns  the target body collector for the boolean operation
             <br>  Created in NX1926.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::ScCollector * TargetBodyCollector
            (
            );
            /**Sets  the target body collector for the boolean operation
             <br>  Created in NX1926.0.0.  <br>
             <br> License requirements : None */
            public: void SetTargetBodyCollector
            (
                NXOpen::ScCollector * targetBodyCollector /** targetbodycollector */
            /**Returns  the copy targets flag
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : None */
            public: bool CopyTargets
            (
            );
            /**Sets  the copy targets flag
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetCopyTargets
            (
                bool copyTargets /** copytargets */
             <br>  Created in NX5.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetCopyTargets
            (
                bool copyTargets /** copytargets */
            );
            /**Returns  the copy tools flag
            /**Returns  the remove target voids flag for Transfer Voids
             <br>  Created in NX2412.0.0.  <br>
             <br> License requirements : None */
            public: bool RemoveTargetVoids
            (
            );
            /**Sets  the remove target voids flag for Transfer Voids
             <br>  Created in NX2412.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetRemoveTargetVoids
            (
                bool removeTargetVoids /** removetargetvoids */
             <br>  Created in NX2412.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") */
            public: void SetRemoveTargetVoids
            (
                bool removeTargetVoids /** removetargetvoids */
            );
        };
```

## BlockFeatureBuilder
File: `Features_BlockFeatureBuilder.hxx`

```cpp
                    is specified by the input origin point in absolute coordinates. The orientation of the block is along
                    the x, y, and z axes of the WCS.
             <br>  Created in NX3.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR features_modeling ("FEATURES MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") */
            public: void SetOriginAndLengths
            (
                const NXOpen::Point3d & originPoint /** Block origin point */,
                    is specified by the input origin point in absolute coordinates. The orientation of the block is along
                    the x, y, and z axes of the WCS.
             <br>  Created in NX3.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR features_modeling ("FEATURES MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") */
            void SetOriginAndLengths
            (
                const NXOpen::Point3d & originPoint /** Block origin point */,
            /** Create a block by setting the block height and two diagonal points in the WCS x-y plane. The orientation
                    of the block is along the x, y, and z axes of the WCS.
             <br>  Created in NX3.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR features_modeling ("FEATURES MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") */
            public: void SetTwoPointsAndHeight
            (
                const NXOpen::Point3d & originPoint /** Block origin point */,
            /** Create a block by setting the block height and two diagonal points in the WCS x-y plane. The orientation
                    of the block is along the x, y, and z axes of the WCS.
             <br>  Created in NX3.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR features_modeling ("FEATURES MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") */
            void SetTwoPointsAndHeight
            (
                const NXOpen::Point3d & originPoint /** Block origin point */,
            /**Returns  the boolean option
             <br>  Created in NX6.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::GeometricUtilities::BooleanOperation * BooleanOption
            (
            );
```

## ScRuleFactory
File: `ScRuleFactory.hxx`

```cpp
        /** Get the type of selection intent rule: @link  NXOpen::SelectionIntentRuleOptions   NXOpen::SelectionIntentRuleOptions @endlink
         <br>  Created in NX1953.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::SelectionIntentRuleOptions * CreateRuleOptions
        (
        );
        /** Creates selection intent rule: @link  NXOpen::CurveDumbRule   NXOpen::CurveDumbRule @endlink   @return
         <br>  Created in NX3.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::CurveDumbRule * CreateRuleCurveDumb
        (
            const std::vector<NXOpen::Curve *> & curves /** Curves which creates this rule. */
        /** Creates selection intent rule: @link  NXOpen::CurveDumbRule   NXOpen::CurveDumbRule @endlink   @return
         <br>  Created in NX1953.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::CurveDumbRule * CreateRuleCurveDumb
        (
            const std::vector<NXOpen::Curve *> & curves /** Curves which creates this rule. */,
        /** Creates selection intent rule: @link  NXOpen::CurveDumbRule   NXOpen::CurveDumbRule @endlink   @return
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::CurveDumbRule * CreateRuleCurveDumbFromPoints
        (
            const std::vector<NXOpen::Point *> & points /** Points which creates this rule. */
        /** Creates selection intent rule: @link  NXOpen::CurveDumbRule   NXOpen::CurveDumbRule @endlink   @return
         <br>  Created in NX1953.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::CurveDumbRule * CreateRuleCurveDumbFromPoints
        (
            const std::vector<NXOpen::Point *> & points /** Points which creates this rule. */,
        /** Creates selection intent rule: @link  NXOpen::RegionBoundaryRule   NXOpen::RegionBoundaryRule @endlink   @return
         <br>  Created in NX6.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::RegionBoundaryRule * CreateRuleRegionBoundary
        (
            NXOpen::DisplayableObject * seedObj /** face or sketch */,
        /** Creates selection intent rule: @link  NXOpen::RegionBoundaryRule   NXOpen::RegionBoundaryRule @endlink   @return
         <br>  Created in NX1953.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::RegionBoundaryRule * CreateRuleRegionBoundary
        (
            NXOpen::DisplayableObject * seedObj /** face or sketch */,
        /** Creates selection intent rule: @link  NXOpen::BodyDumbRule   NXOpen::BodyDumbRule @endlink   @return
         <br>  Created in NX7.5.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::BodyDumbRule * CreateRuleBodyDumb
        (
            const std::vector<NXOpen::Body *> & bodies /** Bodies used to create this rule. */
        /** Creates selection intent rule: @link  NXOpen::BodyDumbRule   NXOpen::BodyDumbRule @endlink  with the option to include or exclude sheet bodies  @return
         <br>  Created in NX9.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::BodyDumbRule * CreateRuleBodyDumb
        (
            const std::vector<NXOpen::Body *> & bodies /** Bodies used to create this rule. */,
        /** Creates selection intent rule: @link  NXOpen::BodyDumbRule   NXOpen::BodyDumbRule @endlink  with the option to include or exclude sheet bodies  @return
         <br>  Created in NX1953.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NXOpen::BodyDumbRule * CreateRuleBodyDumb
        (
            const std::vector<NXOpen::Body *> & bodies /** Bodies used to create this rule. */,
```

## Section
File: `Section.hxx`

```cpp
    end_connector_intersection_point: The point of intersection of the "chained_entity" and the
    "end_connector". This is used to determine what portion of the chain to use in case the "end_connector"
    intersects the "chained_entity" in multiple locations.
     <br>
     <br> To create a new instance of this class, use @link NXOpen::SectionCollection::CreateSection  NXOpen::SectionCollection::CreateSection @endlink  <br>
     <br>  Created in NX3.0.0.  <br>
    */
        /** Adds selection intent rules to the section.
         <br>  Created in NX4.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: void AddToSection
        (
            const std::vector<NXOpen::SelectionIntentRule *> & rules /** Selection intent rules. To create selection intent rules see
        /** Adds selection intent rules to the section with the option of restricting
                chaining and limit discovery to a single feature.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: void AddToSection
        (
            const std::vector<NXOpen::SelectionIntentRule *> & rules /** Selection intent rules. To create selection intent rules see
        /** Add smart point into section.
             <br>
            This API is now deprecated.
            Please use @link ScRuleFactory::CreateRuleCurveDumb ScRuleFactory::CreateRuleCurveDumb@endlink  and @link Section::AddToSection Section::AddToSection@endlink  instead.
             <br>
            This API is now deprecated.
            Please use @link ScRuleFactory::CreateRuleCurveDumb ScRuleFactory::CreateRuleCurveDumb@endlink  and @link Section::AddToSection Section::AddToSection@endlink  instead.
             <br>
         <br>  @deprecated Deprecated in NX7.5.0.  Please use @link ScRuleFactory::CreateRuleCurveDumb ScRuleFactory::CreateRuleCurveDumb@endlink  followed by @link Section::AddToSection Section::AddToSection@endlink  instead. <br>
         <br>  Created in NX4.0.0.  <br>
         <br>  @deprecated Deprecated in NX7.5.0.  Please use @link ScRuleFactory::CreateRuleCurveDumb ScRuleFactory::CreateRuleCurveDumb@endlink  followed by @link Section::AddToSection Section::AddToSection@endlink  instead. <br>
         <br>  Created in NX4.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: NX_DEPRECATED("Deprecated in NX7.5.0.  Please use ScRuleFactory::CreateRuleCurveDumb followed by Section::AddToSection instead.") void AddSmartPoint
        (
            NXOpen::Point * smartPt /** Smart point tobe added into section. */,
        /** Allow self intersecting section or not. By default self intersection is allowed.
         <br>  Created in NX4.0.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: void AllowSelfIntersection
        (
            bool allowSelfIntersection /** True if self-intersecting section is allowed else false*/
             <br>
         <br>  Created in NX7.5.0.  <br>
         <br> License requirements : gateway ("UG GATEWAY") */
        public: void SetAllowedEntityTypes
        (
            NXOpen::Section::AllowTypes allowedEntityTypes /** Allowed entity types. */
```

## SketchInPlaceBuilder
File: `SketchInPlaceBuilder.hxx`

```cpp
    /**
        Use the @link NXOpen::SketchInPlaceBuilder NXOpen::SketchInPlaceBuilder@endlink  to create or reattach a @link NXOpen::Sketch NXOpen::Sketch@endlink  on a @link NXOpen::DatumPlane NXOpen::DatumPlane@endlink  or planar @link NXOpen::Face NXOpen::Face@endlink .
         <br> To create a new instance of this class, use @link NXOpen::SketchCollection::CreateSketchInPlaceBuilder2  NXOpen::SketchCollection::CreateSketchInPlaceBuilder2 @endlink  <br>
    Default values.
    <list type="table">
        /**Returns  the specified sketch plane
         <br>  @deprecated Deprecated in NX11.0.0.  Use @link NXOpen::SketchInPlaceBuilder::PlaneReference NXOpen::SketchInPlaceBuilder::PlaneReference@endlink  instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br>  @deprecated Deprecated in NX11.0.0.  Use @link NXOpen::SketchInPlaceBuilder::PlaneReference NXOpen::SketchInPlaceBuilder::PlaneReference@endlink  instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NX_DEPRECATED("Deprecated in NX11.0.0.  Use NXOpen::SketchInPlaceBuilder::PlaneReference instead.") NXOpen::SelectISurface * PlaneOrFace
        (
        );
        /**Returns  the specified datum plane
         <br>  @deprecated Deprecated in NX11.0.0.  Use @link NXOpen::SketchInPlaceBuilder::PlaneReference NXOpen::SketchInPlaceBuilder::PlaneReference@endlink  instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br>  @deprecated Deprecated in NX11.0.0.  Use @link NXOpen::SketchInPlaceBuilder::PlaneReference NXOpen::SketchInPlaceBuilder::PlaneReference@endlink  instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NX_DEPRECATED("Deprecated in NX11.0.0.  Use NXOpen::SketchInPlaceBuilder::PlaneReference instead.") NXOpen::Plane * Plane
        (
        );
        /**Sets  the flag to indicate the normal direction of the sketch plane is reversed.  This is not applicable when the plane is a Face.
         <br>  @deprecated Deprecated in NX11.0.0.  Get NXOpen.SketchInPlaceBuilder.PlaneReference, and then reverse the smart plane normal. <br>
         <br>  Created in NX5.0.0.  <br>
         <br>  @deprecated Deprecated in NX11.0.0.  Get NXOpen.SketchInPlaceBuilder.PlaneReference, and then reverse the smart plane normal. <br>
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NX_DEPRECATED("Deprecated in NX11.0.0.  Get NXOpen.SketchInPlaceBuilder.PlaneReference, and then reverse the smart plane normal.") void SetReversePlaneNormal
        (
            bool reversePlaneNormal /** reverseplanenormal */
        /**Returns  the placement plane for sketch
         <br>  Created in NX11.0.0.  <br>
         <br> License requirements : None */
        public: NXOpen::Plane * PlaneReference
        (
        );
        /**Sets  the placement plane for sketch
         <br>  Created in NX11.0.0.  <br>
         <br> License requirements : solid_modeling ("SOLIDS MODELING") OR cam_base ("CAM BASE") OR geometric_tol ("GDT") OR nx_freeform_1 ("basic freeform modeling") */
        public: void SetPlaneReference
        (
            NXOpen::Plane * plane /** plane */
```

## FileNew
File: `FileNew.hxx`

```cpp
    /**
        The application type of the new file being created through a template
     <br>  @deprecated Deprecated in NX9.0.0.  Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  that returns all application names. <br>
    */
    enum NX_DEPRECATED("Deprecated in NX9.0.0.  Use NXOpen::FileNew::GetApplicationNames that returns all application names.") FileNewApplication
        The application type of the new file being created through a template
     <br>  @deprecated Deprecated in NX9.0.0.  Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  that returns all application names. <br>
    */
    enum NX_DEPRECATED("Deprecated in NX9.0.0.  Use NXOpen::FileNew::GetApplicationNames that returns all application names.") FileNewApplication
    {
        FileNewApplicationDrafting/** Specifies a drafting file new template */,
        /**Returns  the name of the new file being created
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NXString NewFileName
        (
        );
        /**Sets  the name of the new file being created
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: void SetNewFileName
        (
            const NXString & fileName /** filename */
        /**Sets  the name of the new file being created
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        void SetNewFileName
        (
            const char * fileName /** filename */
        /**Returns  the name of the template part from which to create the new file
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NXString TemplateFileName
        (
        );
        /**Sets  the name of the template part from which to create the new file
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: void SetTemplateFileName
        (
            const NXString & templateFileName /** templatefilename */
        /**Sets  the name of the template part from which to create the new file
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        void SetTemplateFileName
        (
            const char * templateFileName /** templatefilename */
        /**Returns  the units for the new file being created
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NXOpen::Part::Units Units
        (
        );
        /**Sets  the units for the new file being created
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: void SetUnits
        (
            NXOpen::Part::Units units /** units */
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: void SetUnits
        (
            NXOpen::Part::Units units /** units */
        );
        /**Returns  the application type for the new file being created
        /**Returns  the application type for the new file being created
         <br>  @deprecated Deprecated in NX9.0.0.  Use @link NXOpen::FileNew::ApplicationName NXOpen::FileNew::ApplicationName@endlink  that takes a string name instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br>  @deprecated Deprecated in NX9.0.0.  Use @link NXOpen::FileNew::ApplicationName NXOpen::FileNew::ApplicationName@endlink  that takes a string name instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NX_DEPRECATED("Deprecated in NX9.0.0.  Use NXOpen::FileNew::ApplicationName that takes a string name instead.") NXOpen::FileNewApplication Application
        (
        );
        /**Sets  the application type for the new file being created
         <br>  @deprecated Deprecated in NX9.0.0.  Use @link NXOpen::FileNew::SetApplicationName NXOpen::FileNew::SetApplicationName@endlink  that takes a string name instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br>  @deprecated Deprecated in NX9.0.0.  Use @link NXOpen::FileNew::SetApplicationName NXOpen::FileNew::SetApplicationName@endlink  that takes a string name instead. <br>
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NX_DEPRECATED("Deprecated in NX9.0.0.  Use NXOpen::FileNew::SetApplicationName that takes a string name instead.") void SetApplication
        (
            NXOpen::FileNewApplication application /** application */
        /**Returns  the application type for the new file being created
                     Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  to get valid application names.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        /**Returns  the application type for the new file being created
                     Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  to get valid application names.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: NXString ApplicationName
        (
        );
        /**Sets  the application type for the new file being created
                     Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  to get valid application names.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        /**Sets  the application type for the new file being created
                     Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  to get valid application names.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        public: void SetApplicationName
        (
            const NXString & application /** application */
        /**Sets  the application type for the new file being created
                     Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  to get valid application names.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        /**Sets  the application type for the new file being created
                     Use @link NXOpen::FileNew::GetApplicationNames NXOpen::FileNew::GetApplicationNames@endlink  to get valid application names.
         <br>  Created in NX5.0.0.  <br>
         <br> License requirements : None */
        void SetApplicationName
        (
            const char * application /** application */
        /**Returns  the property that controls if the new file should be created using a blank template.
                If set to False, then a valid file name for an existing template part file must be supplied to
                @link NXOpen::FileNew::SetTemplateFileName NXOpen::FileNew::SetTemplateFileName@endlink .  If set to True, this means that no template
                is used during creation.
        /**Sets  the property that controls if the new file should be created using a blank template.
                If set to False, then a valid file name for an existing template part file must be supplied to
                @link NXOpen::FileNew::SetTemplateFileName NXOpen::FileNew::SetTemplateFileName@endlink .  If set to True, this means that no template
                is used during creation.
            const char * usesMasterModel /** usesmastermodel */
        );
        /** Returns all registered application names. These name should be used while setting the application name in @link SetApplicationName SetApplicationName@endlink . @return  All registered application names
         <br>  Created in NX9.0.0.  <br>
         <br> License requirements : None */
        /** Returns all registered application names. These name should be used while setting the application name in @link SetApplicationName SetApplicationName@endlink . @return  All registered application names
         <br>  Created in NX9.0.0.  <br>
         <br> License requirements : None */
        public: std::vector<NXString> GetApplicationNames
        (
        );
        /** Returns @link NXOpen::FileNewTemplate NXOpen::FileNewTemplate@endlink  file new templates which match with given properties like File New Application
                    @link NXOpen::FileNewApplication NXOpen::FileNewApplication@endlink  and part units @link NXOpen::Part::Units NXOpen::Part::Units@endlink . If an invalid File New Application
                    value is supplied as input to this API then it will not return any template. If JA_PART_units_mix is supplied as input to 'units' argument
                    then all unit's templates of given File New Application are returned. @return  Need to free it.
            NXOpen::FileNewApplication application /** application */ ,
            NXOpen::Part::Units units /** units */
        );
```

## BooleanOperation
File: `GeometricUtilities_BooleanOperation.hxx`

```cpp
            /** Boolean operation type. */
            public: enum BooleanType
            {
                BooleanTypeCreate/** Create */,
            /** Boolean operation type. */
            public: enum BooleanType
            {
                BooleanTypeCreate/** Create */,
                BooleanTypeUnite/** Unite */,
                BooleanTypeSubtract/** Subtract */,
                BooleanTypeCreate/** Create */,
                BooleanTypeUnite/** Unite */,
                BooleanTypeSubtract/** Subtract */,
                BooleanTypeIntersect/** Intersect */,
                BooleanTypeUnite/** Unite */,
                BooleanTypeSubtract/** Subtract */,
                BooleanTypeIntersect/** Intersect */,
                BooleanTypeSew/** Sew */
                BooleanTypeSubtract/** Subtract */,
                BooleanTypeIntersect/** Intersect */,
                BooleanTypeSew/** Sew */
            };
                BooleanTypeIntersect/** Intersect */,
                BooleanTypeSew/** Sew */
            };
            /**  Get the Boolean operation type and target body
             <br>  @deprecated Deprecated in NX4.0.0.  Use @link GeometricUtilities::BooleanOperation::Type GeometricUtilities::BooleanOperation::Type@endlink  and @link GeometricUtilities::BooleanOperation::GetTargetBodies GeometricUtilities::BooleanOperation::GetTargetBodies@endlink  instead. <br>
             <br>  Created in NX3.0.1.  <br>
             <br>  @deprecated Deprecated in NX4.0.0.  Use @link GeometricUtilities::BooleanOperation::Type GeometricUtilities::BooleanOperation::Type@endlink  and @link GeometricUtilities::BooleanOperation::GetTargetBodies GeometricUtilities::BooleanOperation::GetTargetBodies@endlink  instead. <br>
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : None */
            public: NX_DEPRECATED("Deprecated in NX4.0.0.  Use GeometricUtilities::BooleanOperation::Type and GeometricUtilities::BooleanOperation::GetTargetBodies instead.") void GetBooleanOperationAndBody
            (
                NXOpen::GeometricUtilities::BooleanOperation::BooleanType* type /** boolean type */,
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : None */
            public: NX_DEPRECATED("Deprecated in NX4.0.0.  Use GeometricUtilities::BooleanOperation::Type and GeometricUtilities::BooleanOperation::GetTargetBodies instead.") void GetBooleanOperationAndBody
            (
                NXOpen::GeometricUtilities::BooleanOperation::BooleanType* type /** boolean type */,
                NXOpen::Body ** targetBody /** target body */
            );
            /**  Set the Boolean operation type and target body
             <br>  @deprecated Deprecated in NX4.0.0.  Use @link GeometricUtilities::BooleanOperation::SetType GeometricUtilities::BooleanOperation::SetType@endlink  and @link GeometricUtilities::BooleanOperation::SetTargetBodies GeometricUtilities::BooleanOperation::SetTargetBodies@endlink  instead. <br>
             <br>  Created in NX3.0.1.  <br>
             <br>  @deprecated Deprecated in NX4.0.0.  Use @link GeometricUtilities::BooleanOperation::SetType GeometricUtilities::BooleanOperation::SetType@endlink  and @link GeometricUtilities::BooleanOperation::SetTargetBodies GeometricUtilities::BooleanOperation::SetTargetBodies@endlink  instead. <br>
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") */
            public: NX_DEPRECATED("Deprecated in NX4.0.0.  Use GeometricUtilities::BooleanOperation::SetType and GeometricUtilities::BooleanOperation::SetTargetBodies instead.") void SetBooleanOperationAndBody
            (
                NXOpen::GeometricUtilities::BooleanOperation::BooleanType type /** boolean type */,
             <br>  Created in NX3.0.1.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") */
            public: NX_DEPRECATED("Deprecated in NX4.0.0.  Use GeometricUtilities::BooleanOperation::SetType and GeometricUtilities::BooleanOperation::SetTargetBodies instead.") void SetBooleanOperationAndBody
            (
                NXOpen::GeometricUtilities::BooleanOperation::BooleanType type /** boolean type */,
                NXOpen::Body * targetBody /** target body */
            );
            /**Returns   the boolean operation type
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : None */
            public: NXOpen::GeometricUtilities::BooleanOperation::BooleanType Type
            (
            );
            /**Sets   the boolean operation type
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") OR nx_freeform_1 ("basic freeform modeling") */
            public: void SetType
            (
                NXOpen::GeometricUtilities::BooleanOperation::BooleanType type /** boolean type */
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") OR nx_freeform_1 ("basic freeform modeling") */
            public: void SetType
            (
                NXOpen::GeometricUtilities::BooleanOperation::BooleanType type /** boolean type */
            );
            /**  Get the target bodies
            /**  Set the target bodies
             <br>  Created in NX4.0.0.  <br>
             <br> License requirements : solid_modeling ("SOLIDS MODELING") OR cam_base ("CAM BASE") OR insp_programming ("INSPECTION PROGRAMMING") OR nx_freeform_1 ("basic freeform modeling") */
            public: void SetTargetBodies
            (
                const std::vector<NXOpen::Body *> & targetBodies /**  target bodies of boolean */
```
