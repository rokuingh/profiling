! Earth System Modeling Framework
! Copyright 2002-2020, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the University of Illinois-NCSA License.

! #define profile_mesh_create
! #define profile_mesh_redist
! #define profile_mesh_destroy

program MOAB_eval_redist

  use ESMF
  implicit none
  logical :: correct
  integer :: localrc
  integer :: localPet, petCount
  type(ESMF_VM) :: vm
  character(ESMF_MAXPATHLEN) :: srcfile
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
  if (numargs .ne. 1) then
     write(*,*) "ERROR: MOAB_eval Should be run with 1 argument"
     stop
  endif

  ! Get filenames
    call ESMF_UtilGetArg(1, argvalue=srcfile, rc=localrc)
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
     write(*,*) "REDIST on ",trim(srcfile)
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
  call profile_mesh_redist(srcfile, moab=.false., rc=localrc)
   if (localrc /=ESMF_SUCCESS) then
     write(*,*) "ERROR IN REDIST SUBROUTINE!"
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
  call profile_mesh_redist(srcfile, moab=.true., rc=localrc)
   if (localrc /=ESMF_SUCCESS) then
     write(*,*) "ERROR IN REDIST SUBROUTINE!"
          stop
    endif
  
  ! Finalize ESMF
  call ESMF_Finalize(rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
     stop
  endif

  contains


 subroutine profile_mesh_redist(srcfile, moab, rc)
  character(len=*) :: srcfile
  logical, intent(in) :: moab
  integer, intent(out)  :: rc

  integer :: localrc
  character(12) :: NM
  type(ESMF_VM) :: vm
  type(ESMF_Mesh) :: srcMesh, redistMesh
  type(ESMF_DistGrid) :: distgrid1, distgrid2, distgrid3

  integer :: i
  integer, allocatable :: ec(:)
  integer, allocatable :: sil(:)
  integer, allocatable :: asil(:)

  ! grid sizes are hardcoded, just easier this way
  ! integer, parameter :: numNode = 1639680  ! ll1280x1280_grid.esmf.nc
  integer, parameter :: numNode = 6480 ! ll80x80_grid.esmf.nc
  integer :: minI, maxI, nn

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

  NM = "NVMesh"
  if (moab) then
    NM = "MBMesh"
  endif


  nn = numNode/petCount
  
  minI = localPet*nn + 1
  maxI = (localPet+1)*nn
  if (localPet == petCount-1) maxI = numNode

  allocate(asil(maxI-minI+1))
  do i=1,maxI-minI+1
    asil(i) = minI + i - 1
  enddo

  distgrid1 = ESMF_DistGridCreate(arbSeqIndexList=asil, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! print *, localPet, "# distgrid1 minI = ", minval(asil), " maxI = ", maxval(asil)
  deallocate(asil)

  minI = (petCount - localPet - 1)*nn + 1
  maxI = (petCount - localPet)*nn
  if (localPet == 0) maxI = numNode

  allocate(asil(maxI-minI+1))
  do i=1,maxI-minI+1
    asil(i) = minI + i - 1
  enddo

  distgrid2 = ESMF_DistGridCreate(arbSeqIndexList=asil, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

  ! print *, localPet, "# distgrid2 minI = ", minval(asil), " maxI = ", maxval(asil)
  deallocate(asil)

#define profile_mesh_create
#ifdef profile_mesh_create
  call ESMF_TraceRegionEnter(NM//" Create")
  call ESMF_VMLogMemInfo("before "//NM//" create")
#endif

  srcMesh=ESMF_MeshCreate(filename=srcfile, fileformat=ESMF_FILEFORMAT_ESMFMESH, &
                          nodalDistgrid=distgrid1, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

!   call ESMF_MeshGet(srcMesh, nodalDistgrid=distgrid1, rc=localrc)
!   if (localrc /=ESMF_SUCCESS) then
!     rc=ESMF_FAILURE
!     return
!   endif
! 
!   allocate(ec(4))
!   call ESMF_DistGridGet(distgrid1, elementCountPDe=ec, rc=localrc)
!   if (localrc /=ESMF_SUCCESS) then
!     rc=ESMF_FAILURE
!     return
!   endif
! 
!   allocate(sil(ec(localPet+1)))
!   call ESMF_DistGridGet(distgrid1, 0, seqIndexList=sil, rc=localrc)
!   if (localrc /=ESMF_SUCCESS) then
!     rc=ESMF_FAILURE
!     return
!   endif
! 
! print *, localPet, "# distgrid actual minI = ", minval(sil), " maxI = ", maxval(sil)

#ifdef profile_mesh_create
  call ESMF_VMLogMemInfo("after "//NM//" create")
  call ESMF_TraceRegionExit(NM//" Create")
#endif

! remove the complete redist, as sufficient redist with create to demonstrate timing profile issue
#if 0

#ifdef profile_mesh_redist
  call ESMF_TraceRegionEnter(NM//" Redist")
  call ESMF_VMLogMemInfo("before "//NM//" redist")

  redistMesh = ESMF_MeshCreate(srcMesh, nodalDistgrid=distgrid2, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif


  call ESMF_VMLogMemInfo("after "//NM//" redist")
  call ESMF_TraceRegionExit(NM//" Redist")
#endif

#endif

#ifdef profile_mesh_destroy
  call ESMF_TraceRegionEnter(NM//" Destroy")
  call ESMF_VMLogMemInfo("before "//NM//" destroy")
#endif

  ! Free the meshes
  call ESMF_MeshDestroy(srcMesh, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#ifdef profile_mesh_destroy
  call ESMF_VMLogMemInfo("after "//NM//" destroy")
  call ESMF_TraceRegionExit(NM//" Destroy")
#endif

#endif
! ESMF_MOAB

end subroutine profile_mesh_redist

end program MOAB_eval_redist

