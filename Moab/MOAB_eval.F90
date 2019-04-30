! $Id:  Exp $
!
! Earth System Modeling Framework
! Copyright 2002-2015, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the University of Illinois-NCSA License.
!


#define CHECK_ACCURACY
! #define OUTPUT_ERROR

! define one of the following regrid methods
! #define CONSERVE
! #define BILINEAR_CENTERS
#define BILINEAR_CORNERS


program MOAB_eval

  use ESMF
  implicit none
  logical :: correct
  integer :: localrc
  integer :: localPet, petCount
  type(ESMF_VM) :: vm
  character(ESMF_MAXPATHLEN) :: srcfile, dstfile
  integer :: numargs

   ! Init ESMF
  call ESMF_Initialize(rc=localrc, logappendflag=.false.)
  if (localrc /=ESMF_SUCCESS) then
     stop
  endif

  ! Error check number of command line args
  call ESMF_UtilGetArgC(count=numargs, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    stop
  endif
  if (numargs .ne. 2) then
     write(*,*) "ERROR: MOAB_eval Should be run with 2 arguments"
     stop
  endif

  ! Get filenames
    call ESMF_UtilGetArg(1, argvalue=srcfile, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    stop
  endif


  ! Get filenames
  call ESMF_UtilGetArg(2, argvalue=dstfile, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    stop
  endif


  ! get pet info
   call ESMF_VMGetGlobal(vm, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    stop
  endif

  call ESMF_VMGet(vm, petCount=petCount, localPet=localpet, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    stop
  endif

  ! Write out number of PETS
  if (localPet .eq. 0) then
     write(*,*)
     write(*,*) "REGRIDDING FROM ",trim(srcfile)," TO ",trim(dstfile)
     write(*,*) "NUMBER OF PROCS = ",petCount
     write(*,*)
  endif


  !!!!!!!!!!!!!!! Time Native Mesh !!!!!!!!!!!!
  if (localPet .eq. 0) then
     write(*,*) "======= Native ESMF Mesh ======="
  endif
  
  ! Make sure  MOAB is off
    call ESMF_MeshSetMOAB(.false., rc=localrc)
  if (localrc .ne. ESMF_SUCCESS) then
     stop
  endif
  
  
  ! Regridding using ESMF native Mesh
  call time_mesh_regrid(srcfile, dstfile, moab=.false., rc=localrc)
   if (localrc /=ESMF_SUCCESS) then
     write(*,*) "ERROR IN REGRIDDING SUBROUTINE!"
     stop
  endif

  !!!!!!!!!!!!!!! Time MOAB Mesh !!!!!!!!!!!!
  if (localPet .eq. 0) then
     write(*,*)
     write(*,*)
     write(*,*) "======= MOAB Mesh ======="
  endif
  
  ! Turn on MOAB
  call ESMF_MeshSetMOAB(.true., rc=localrc)
  if (localrc .ne. ESMF_SUCCESS) then
     stop
  endif
  
  ! Regridding using MOAB Mesh
  call time_mesh_regrid(srcfile, dstfile, moab=.true., rc=localrc)
   if (localrc /=ESMF_SUCCESS) then
     write(*,*) "ERROR IN REGRIDDING SUBROUTINE!"
          stop
    endif
  
  ! Finalize ESMF
  call ESMF_Finalize(rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
     stop
  endif

  contains


  subroutine compute_max_avg_time(in, max, avg, rc)
    real(ESMF_KIND_R8) :: in,max,avg
    type(ESMF_VM) :: vm
    real(ESMF_KIND_R8) :: in_array(1)
    real(ESMF_KIND_R8) :: in_max_array(1)
    real(ESMF_KIND_R8) :: in_sum_array(1)
    integer :: localrc, rc, petCount, localPet

    ! get pet info
    call ESMF_VMGetGlobal(vm, rc=localrc)
    if (localrc .ne. ESMF_SUCCESS) then
       rc=ESMF_FAILURE
       return
    endif

    call ESMF_VMGet(vm, petCount=petCount, localPet=localpet, rc=localrc)
    if (localrc .ne. ESMF_SUCCESS) then
       rc=ESMF_FAILURE
       return
    endif

    in_array(1)=in

    call ESMF_VMAllReduce(vm, in_array, in_sum_array, 1, &
         ESMF_REDUCE_SUM, rc=localrc)
    if (localrc /=ESMF_SUCCESS) then
       rc=ESMF_FAILURE
       return
    endif

    call ESMF_VMAllReduce(vm, in_array, in_max_array, 1, &
         ESMF_REDUCE_MAX, rc=localrc)
    if (localrc /=ESMF_SUCCESS) then
       rc=ESMF_FAILURE
       return
    endif

    ! do output
    avg=in_sum_array(1)/REAL(petCount,ESMF_KIND_R8)
    max=in_max_array(1)

  end subroutine compute_max_avg_time



 subroutine time_mesh_regrid(srcfile, dstfile, moab, rc)
  character(len=*) :: srcfile, dstfile
  logical, intent(in) :: moab
  integer, intent(out)  :: rc

  integer :: localrc
  character(12) :: NM
  type(ESMF_DistGrid) :: distgrid
  type(ESMF_Mesh) :: srcMesh
  type(ESMF_Mesh) :: dstMesh
  type(ESMF_Field) :: srcField
  type(ESMF_Field) :: dstField
  type(ESMF_Field) :: xdstField
  type(ESMF_Field) :: srcAreaField, dstAreaField
  type(ESMF_Field) :: srcFracField, dstFracField
  type(ESMF_RouteHandle) :: routeHandle
  type(ESMF_ArraySpec) :: arrayspec
  type(ESMF_VM) :: vm
  real(ESMF_KIND_R8), pointer :: srcFarrayPtr(:), dstFarrayPtr(:), xdstFarrayPtr(:)
  real(ESMF_KIND_R8), pointer :: srcAreaPtr(:), dstAreaPtr(:)
  real(ESMF_KIND_R8), pointer :: srcFracPtr(:), dstFracPtr(:)
  integer :: clbnd(1),cubnd(1)
  integer, allocatable :: seqIndexList(:)
  integer :: id, lcount
  
  integer :: i1,i2,i3
  real(ESMF_KIND_R8) :: x,y,z
  integer :: localPet, petCount
  real(ESMF_KIND_R8) :: srcmass(1), dstmass(1), srcmassg(1), dstmassg(1)
  real(ESMF_KIND_R8) :: maxerror(1), minerror(1), error
  real(ESMF_KIND_R8) :: maxerrorg(1), minerrorg(1), errorg

  real(ESMF_KIND_R8) :: errorTot, errorTotG

  integer, pointer :: nodeIds(:),nodeOwners(:)
  real(ESMF_KIND_R8), pointer :: nodeCoords(:)
  integer, pointer :: elemIds(:),elemTypes(:),elemConn(:),elemMask(:)
       integer :: numNodes
  integer :: iconn,inode
  integer :: numQuadElems,numTriElems
  integer :: numPentElems,numHexElems,numTotElems
  integer :: numElemConn
  real(ESMF_KIND_R8) :: beg_time, end_time
  real(ESMF_KIND_R8) :: max_time, avg_time
  real(ESMF_KIND_R8), pointer :: srcOwnedCoords(:)
  integer :: srcNumOwned
  integer :: srcSpatialDim
  real(ESMF_KIND_R8), pointer :: dstOwnedCoords(:)
  integer :: dstNumOwned
  integer :: dstSpatialDim
  integer :: cInd


  real(ESMF_KIND_R8), parameter :: UNINITVAL = 1E-20
  integer(ESMF_KIND_I4) :: unmapped_count(1), unmapped_countg(1)
  real(ESMF_KIND_R8),parameter :: DEG2RAD = 3.141592653589793_ESMF_KIND_R8/180.0_ESMF_KIND_R8
  real(ESMF_KIND_R8) :: theta, phi
  real(ESMF_KIND_R8) :: lat, lon

  ! result code
  integer :: finalrc

    ! Init to success
  rc=ESMF_SUCCESS

  ! Don't do the test is MOAB isn't available
#ifdef ESMF_MOAB

  ! get pet info
  call ESMF_VMGetGlobal(vm, rc=localrc)
  if (localrc .ne. ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMGet(vm, petCount=petCount, localPet=localpet, rc=localrc)
  if (localrc .ne. ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  NM = "Native Mesh"
  if (moab) then
    NM = "MOAB Mesh"
  endif

  call ESMF_TraceRegionEnter(NM//" Source Create")
  call ESMF_VMLogMemInfo("before "//NM//" src mesh create")

 !!!! Setup source mesh !!!!
 srcMesh=ESMF_MeshCreate(filename=srcfile, &
          fileformat=ESMF_FILEFORMAT_ESMFMESH, &
          rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

    ! write(filename,"(A15,I1,A1,I1)") "OriginalMBMesh.", petCount, ".", localPet
    ! call ESMF_MeshWrite(tempMesh, filename)
    ! write(filename,"(A19,I1,A1,I1)") "OriginalMBMeshDual.", petCount, ".", localPet
    ! call ESMF_MeshWrite(srcMeshDual, filename)
    ! call ESMF_MeshWrite(srcMesh, "DupNativeMesh")

  call ESMF_VMLogMemInfo("after "//NM//" src mesh create")
  call ESMF_TraceRegionExit(NM//" Source Create")

  ! Array spec for fields
  call ESMF_ArraySpecSet(arrayspec, 1, ESMF_TYPEKIND_R8, rc=rc)

#ifdef CONSERVE
  ! Create source field
  srcField = ESMF_FieldCreate(srcMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                              name="source", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create source area field
  srcAreaField = ESMF_FieldCreate(srcMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                                  name="source_area", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create source frac field
  srcFracField = ESMF_FieldCreate(srcMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                                  name="source_frac", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

#ifdef BILINEAR_CENTERS
  ! Create source field
  srcField = ESMF_FieldCreate(srcMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                              name="source", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

! BILINEAR CORNERS
#ifdef BILINEAR_CORNERS
  ! Create source field
  srcField = ESMF_FieldCreate(srcMesh, arrayspec, meshloc=ESMF_MESHLOC_NODE, &
                              name="source", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif


#ifdef CHECK_ACCURACY
  ! Get Information about src coords
#ifdef CONSERVE
  call ESMF_MeshGet(srcMesh, numOwnedElements=srcNumOwned, &
                    spatialDim=srcSpatialDim, rc=localrc)
#endif
#ifdef BILINEAR_CENTERS
  call ESMF_MeshGet(srcMesh, numOwnedElements=srcNumOwned, &
                    spatialDim=srcSpatialDim, rc=localrc)
#endif
#ifdef BILINEAR_CORNERS
  call ESMF_MeshGet(srcMesh, numOwnedNodes=srcNumOwned, &
                    spatialDim=srcSpatialDim, rc=localrc)
#endif
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
   endif

  ! Allocate array to hold src coords
  allocate(srcOwnedCoords(srcSpatialDim*srcNumOwned))

  ! Get src coords
#ifdef CONSERVE
  call ESMF_MeshGet(srcMesh, ownedElemCoords=srcOwnedCoords, rc=localrc)
#endif
#ifdef BILINEAR_CENTERS
  call ESMF_MeshGet(srcMesh, ownedElemCoords=srcOwnedCoords, rc=localrc)
#endif
#ifdef BILINEAR_CORNERS
  call ESMF_MeshGet(srcMesh, ownedNodeCoords=srcOwnedCoords, rc=localrc)
#endif
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! get src pointer
  call ESMF_FieldGet(srcField, 0, srcFarrayPtr, computationalLBound=clbnd, &
                     computationalUBound=cubnd,  rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Set src data
  do i1=clbnd(1),cubnd(1)

    ! Get coords
    cInd=srcSpatialDim*(i1-clbnd(1))+1
    lon=srcOwnedCoords(cInd)
    lat=srcOwnedCoords(cInd+1)

    ! Set the source to be a function of the coordinates
    theta = DEG2RAD*(lon)
    phi = DEG2RAD*(90.-lat)

    ! set src data
    srcFarrayPtr(i1) = 2. + cos(theta)**2.*cos(2.*phi)
    !srcFarrayPtr(i1) = 1.0
  enddo

#endif


  call ESMF_TraceRegionEnter(NM//" Destination Create")
  call ESMF_VMLogMemInfo("before "//NM//" dst mesh create")

  dstMesh=ESMF_MeshCreate(filename=dstfile, &
          fileformat=ESMF_FILEFORMAT_ESMFMESH, &
          rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMLogMemInfo("after "//NM//" dst mesh create")
  call ESMF_TraceRegionExit(NM//" Destination Create")

  ! Array spec
  call ESMF_ArraySpecSet(arrayspec, 1, ESMF_TYPEKIND_R8, rc=rc)

#ifdef CONSERVE
  ! Create dest. field
  dstField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                              name="dest", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create dest. area field
  dstAreaField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                                  name="dest_area", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create dest. frac field
  dstFracField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                                  name="dest_frac", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create exact dest. field
  xdstField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                               name="xdest", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

#ifdef BILINEAR_CENTERS
  ! Create dest. field
  dstField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                              name="dest", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create exact dest. field
  xdstField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_ELEMENT, &
                               name="xdest", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

#ifdef BILINEAR_CORNERS
  ! Create dest. field
  dstField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_NODE, &
                              name="dest", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Create exact dest. field
  xdstField = ESMF_FieldCreate(dstMesh, arrayspec, meshloc=ESMF_MESHLOC_NODE, &
                               name="xdest", rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

#ifdef CHECK_ACCURACY
  ! Get Information about dst coords
#ifdef CONSERVE
  call ESMF_MeshGet(dstMesh, numOwnedElements=dstNumOwned, &
                    spatialDim=dstSpatialDim, rc=localrc)
#endif
#ifdef BILINEAR_CENTERS
  call ESMF_MeshGet(dstMesh, numOwnedElements=dstNumOwned, &
                    spatialDim=dstSpatialDim, rc=localrc)
#endif
#ifdef BILINEAR_CORNERS
  call ESMF_MeshGet(dstMesh, numOwnedNodes=dstNumOwned, &
                    spatialDim=dstSpatialDim, rc=localrc)
#endif
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Allocate array to hold dst coords
  allocate(dstOwnedCoords(dstSpatialDim*dstNumOwned))

  ! Get dst coords
#ifdef CONSERVE
  call ESMF_MeshGet(dstMesh, ownedElemCoords=dstOwnedCoords, rc=localrc)
#endif
#ifdef BILINEAR_CENTERS
  call ESMF_MeshGet(dstMesh, ownedElemCoords=dstOwnedCoords, rc=localrc)
#endif
#ifdef BILINEAR_CORNERS
  call ESMF_MeshGet(dstMesh, ownedNodeCoords=dstOwnedCoords, rc=localrc)
#endif
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! get dst pointer
  call ESMF_FieldGet(dstField, 0, dstFarrayPtr, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! get exact dst pointer
  call ESMF_FieldGet(xdstField, 0, xdstFarrayPtr, computationalLBound=clbnd, &
                     computationalUBound=cubnd,  rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! Set dst data
  do i1=clbnd(1),cubnd(1)

    ! set dst data
    dstFarrayPtr(i1) = UNINITVAL

    ! Get coords
    cInd=dstSpatialDim*(i1-clbnd(1))+1
    lon=dstOwnedCoords(cInd)
    lat=dstOwnedCoords(cInd+1)

    ! Set the source to be a function of the coordinates
    theta = DEG2RAD*(lon)
    phi = DEG2RAD*(90.-lat)

    ! Set dst exact data
    xdstFarrayPtr(i1) = 2. + cos(theta)**2.*cos(2.*phi)
    !xdstFarrayPtr(i1) = 1.0
  enddo

#endif


  !!! Regrid forward from the A grid to the B grid
  call ESMF_TraceRegionEnter(NM//" Regrid Store")
  call ESMF_VMLogMemInfo("before "//NM//" regrid store")

  call ESMF_FieldRegridStore(srcField, dstField=dstField, &
                             routeHandle=routeHandle, &
#ifdef CONSERVE
                             regridmethod=ESMF_REGRIDMETHOD_CONSERVE, &
#else
                             regridmethod=ESMF_REGRIDMETHOD_BILINEAR, &
#endif
!                             polemethod=ESMF_POLEMETHOD_NONE, &
! COMMENT THESE OUT UNTIL THAT PART IS WORKING
!          dstFracField=dstFracField, &
!          srcFracField=srcFracField, &
                             unmappedaction=ESMF_UNMAPPEDACTION_IGNORE, &
                             rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMLogMemInfo("after "//NM//" regrid store")
  call ESMF_TraceRegionExit(NM//" Regrid Store")

  call ESMF_TraceRegionEnter(NM//" Regrid")
  call ESMF_VMLogMemInfo("before "//NM//" regrid")

  ! Do regrid
  call ESMF_FieldRegrid(srcField, dstField, routeHandle, &
                        zeroregion=ESMF_REGION_SELECT, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMLogMemInfo("after "//NM//" regrid")
  call ESMF_TraceRegionExit(NM//" Regrid")

  call ESMF_TraceRegionEnter(NM//" Regrid Release")
  call ESMF_VMLogMemInfo("before "//NM//" regrid release")

  call ESMF_FieldRegridRelease(routeHandle, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMLogMemInfo("after "//NM//" regrid release")
  call ESMF_TraceRegionExit(NM//" Regrid Release")


#ifdef CHECK_ACCURACY

#ifdef CONSERVE
  ! Get the integration weights
  call ESMF_FieldRegridGetArea(srcAreaField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif


  ! Get the integration weights
  call ESMF_FieldRegridGetArea(dstAreaField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

  ! Check if the values are close
  minerror(1) = 100000.
  maxerror(1) = 0.
  error = 0.
  errorTot=0.0
  dstmass(1) = 0.

  ! get dst Field
  call ESMF_FieldGet(dstField, 0, dstFarrayPtr, computationalLBound=clbnd, &
                     computationalUBound=cubnd, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! get exact destination Field
  call ESMF_FieldGet(xdstField, 0, xdstFarrayPtr, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#ifdef CONSERVE
  ! get dst area Field
  call ESMF_FieldGet(dstAreaField, 0, dstAreaPtr, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
     rc=ESMF_FAILURE
     return
  endif


#if 0
  ! get frac Field
  call ESMF_FieldGet(dstFracField, 0, dstFracptr, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif
#endif

#ifdef CONSERVE
  call ESMF_MeshGet(dstMesh, elementDistgrid=distgrid, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

#ifdef BILINEAR_CENTERS
  call ESMF_MeshGet(dstMesh, elementDistgrid=distgrid, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

#ifdef BILINEAR_CORNERS
  call ESMF_MeshGet(dstMesh, nodalDistgrid=distgrid, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif
  
  call ESMF_DistGridGet(distgrid, 0, elementCount=lcount, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
  
  allocate(seqIndexList(lcount))
  call ESMF_DistGridGet(distgrid, 0, seqIndexList=seqIndexList, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
  
  ! destination grid
  !! check relative error
  unmapped_count(1) = 0;
  unmapped_countg(1) = 0;
  do i1=clbnd(1),cubnd(1)
    
    id = seqIndexList(i1)

#ifdef CONSERVE
    ! This is WRONG, shouldn't include Frac
    ! dstmass = dstmass + dstFracptr(i1,i2)*dstAreaptr(i1)*fptr(i1)

    ! Instead do this
    dstmass(1) = dstmass(1) + dstAreaptr(i1)*dstFarrayPtr(i1)


    ! If this destination cell isn't covered by a sig. amount of source, then compute error on it.
    ! (Note that this is what SCRIP does)
    !if (dstFracptr(i1) .lt. 0.999) cycle

    ! write(*,*) i1,"::",dstFarrayPtr(i1),xdstFarrayPtr(i1)
#endif

    ! if value .eq. UNINITVAL
    if (abs (dstFarrayPtr(i1) - UNINITVAL) < 1.0D-12) then
        unmapped_count(1) = unmapped_count(1) + 1
        ! write (*,*) "unmapped point at ", i1
        error = 0
    else
      ! if value .ne. 0 
      if (abs(xdstFarrayPtr(i1)) > 1.0D-12) then
        error=ABS(dstFarrayPtr(i1) - xdstFarrayPtr(i1))/ABS(xdstFarrayPtr(i1))
      else
        error=ABS(dstFarrayPtr(i1) - xdstFarrayPtr(i1))
      endif
    endif

    errorTot=errorTot+error
    if (error > maxerror(1)) then
      maxerror(1) = error
    endif
    if (error < minerror(1)) then
      minerror(1) = error
    endif


#ifdef OUTPUT_ERROR
    ! Get coords
    cInd=dstSpatialDim*(i1-clbnd(1))+1
    lon=dstOwnedCoords(cInd)
    lat=dstOwnedCoords(cInd+1)

    ! Set the source to be a function of the coordinates
    theta = DEG2RAD*(lon)
    phi = DEG2RAD*(90.-lat)

    if (error > 1E-1) then
      ! print *, i1, ", ", lon, ", ", lat
      !print *, " Error = ", error, "Dst = ", dstFarrayPtr(i1), "Xct = ", xdstFarrayPtr(i1)
      errnum = errnum + 1
    endif
    
    if (id == 4323801 ) then
      print *, id, ", ", lon, ", ", lat
    endif

    if (dstFarrayPtr(i1) .eq. UNINITVAL) then
       write (*,*) localPet, ", ", theta, ", ", phi
    endif

#endif
  enddo

  srcmass(1) = 0.

  ! get src pointer
  call ESMF_FieldGet(srcField, 0, srcFarrayPtr, computationalLBound=clbnd, &
                     computationalUBound=cubnd, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#ifdef CONSERVE
  ! get src Field
  call ESMF_FieldGet(srcAreaField, 0, srcAreaptr, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#if 0
  ! get frac Field
  call ESMF_FieldGet(srcFracField, 0, srcFracptr, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

  do i1=clbnd(1),cubnd(1)
!    srcmass(1) = srcmass(1) + srcFracptr(i1)*srcAreaptr(i1)*srcFarrayPtr(i1)
    srcmass(1) = srcmass(1) + srcAreaptr(i1)*srcFarrayPtr(i1)
  enddo


  srcmassg(1) = 0.
  dstmassg(1) = 0.

  call ESMF_VMAllReduce(vm, srcmass, srcmassg, 1, ESMF_REDUCE_SUM, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMAllReduce(vm, dstmass, dstmassg, 1, ESMF_REDUCE_SUM, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

  call ESMF_VMAllReduce(vm, maxerror, maxerrorg, 1, ESMF_REDUCE_MAX, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMAllReduce(vm, minerror, minerrorg, 1, ESMF_REDUCE_MIN, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMAllReduce(vm, unmapped_count, unmapped_countg, 1, ESMF_REDUCE_SUM, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#ifdef OUTPUT_ERROR
  call ESMF_VMAllReduce(vm, errnum, gerrnum, 1, ESMF_REDUCE_SUM, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
  
  
#endif

#if 0
  if (unmapped_countg(1) > 0) then
    call ESMF_MeshWrite(srcMesh,"srcMesh"//NM)
    call ESMF_MeshWrite(dstMesh,"dstMesh"//NM)
  endif
#endif


#endif

  deallocate(seqIndexList)

  ! Destroy the Fields
  call ESMF_FieldDestroy(srcField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_FieldDestroy(dstField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_FieldDestroy(xdstField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif


#ifdef CONSERVE
  call ESMF_FieldDestroy(srcAreaField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_FieldDestroy(dstAreaField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_FieldDestroy(srcFracField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_FieldDestroy(dstFracField, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif
#endif

  call ESMF_TraceRegionEnter(NM//" Source Destroy")
  call ESMF_VMLogMemInfo("before "//NM//" src mesh destroy")

  ! Free the meshes
  call ESMF_MeshDestroy(srcMesh, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMLogMemInfo("after "//NM//" src mesh destroy")
  call ESMF_TraceRegionExit(NM//" Source Destroy")


#ifdef CHECK_ACCURACY
  ! DeAllocate coordinate arrays
  deallocate(srcOwnedCoords)
  deallocate(dstOwnedCoords)
#endif


  call ESMF_TraceRegionEnter(NM//" Destination Destroy")
  call ESMF_VMLogMemInfo("before "//NM//" dst mesh destroy")

  call ESMF_MeshDestroy(dstMesh, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  call ESMF_VMLogMemInfo("after "//NM//" dst mesh destroy")
  call ESMF_TraceRegionExit(NM//" Destination Destroy")

#ifdef CHECK_ACCURACY
  ! Output Accuracy results
  if (localPet == 0) then
    write(*,*)
    write(*,*) unmapped_countg(1), " unmapped points"
    write(*,*) "interp. max. rel. error = ", maxerrorg(1)
#ifdef CONSERVE
    write(*,*) "conserv. rel. error     = ", ABS(dstmassg(1)-srcmassg(1))/srcmassg(1)
#endif
    !write(*,*) "SRC mass = ", srcmassg(1)
    !write(*,*) "DST mass = ", dstmassg(1)
    !write(*,*) "Min Error = ", minerrorg(1)
    write(*,*)
  endif
#endif
#endif

end subroutine time_mesh_regrid

end program MOAB_eval

