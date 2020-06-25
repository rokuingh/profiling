! Earth System Modeling Framework
! Copyright 2002-2020, University Corporation for Atmospheric Research,
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics
! Laboratory, University of Michigan, National Centers for Environmental
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory,
! NASA Goddard Space Flight Center.
! Licensed under the University of Illinois-NCSA License.

! #define profile_meshcreate
! #define profile_meshredist

! numNode = 6480 ! ll80x80_grid.esmf.nc
! numNode = 1639680  ! ll1280x1280_grid.esmf.nc


program MOAB_eval_create

  use ESMF
  implicit none
  logical :: correct
  integer :: localrc
  integer :: localPet, petCount
  type(ESMF_VM) :: vm
  character(ESMF_MAXPATHLEN) :: file
  character(ESMF_MAXPATHLEN) :: numNodeChar
  integer :: numNode
  integer :: numargs

   ! Init ESMF
  call ESMF_Initialize(rc=localrc, logappendflag=.false.)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)

  ! Error check number of command line args
  call ESMF_UtilGetArgC(count=numargs, rc=localrc)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)

  if (numargs .ne. 2) then
     write(*,*) "ERROR: MOAB_eval Should be run with 2 arguments"
     call ESMF_Finalize(endflag=ESMF_END_ABORT)
  endif

  ! Get filenames
  call ESMF_UtilGetArg(1, argvalue=file, rc=localrc)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)

  if (index(trim(file), "ll80x80_grid.esmf.nc") /= 0) then
    numNode = 6480
  elseif (index(trim(file), "ll1280x1280_grid.esmf.nc") /= 0) then
    numNode = 1639680
  else
    call ESMF_Finalize(endflag=ESMF_END_ABORT)
  endif

  ! get pet info
  call ESMF_VMGetGlobal(vm, rc=localrc)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)

  call ESMF_VMGet(vm, petCount=petCount, localPet=localpet, rc=localrc)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)

  ! Write out number of PETS
  if (localPet .eq. 0) then
     write(*,*)
     write(*,*) "NUMBER OF PROCS = ",petCount
     write(*,*) "GRID FILE = ",trim(file)
     write(*,*) "numNode = ", numNode
  endif

  !!!!!!!!!!!!!!! Time NativeMesh !!!!!!!!!!!!
  if (localPet .eq. 0) then
     write(*,*)
     write(*,*) "Running NativeMesh ..."
  endif
  
  ! Make sure  MOAB is off
  call ESMF_MeshSetMOAB(.false., rc=localrc)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)
  
  ! Regridding using ESMF native Mesh
  call profile_mesh_create(.false., file, rc=localrc)
   if (localrc /=ESMF_SUCCESS) then
     write(*,*) "ERROR IN REDIST SUBROUTINE!"
     call ESMF_Finalize(endflag=ESMF_END_ABORT)
  endif

  !!!!!!!!!!!!!!! Time MOAB Mesh !!!!!!!!!!!!
  if (localPet .eq. 0) then
     write(*,*)
     write(*,*) "Running MBMesh ..."
  endif
  
  ! Turn on MOAB
  call ESMF_MeshSetMOAB(.true., rc=localrc)
  if (localrc /= ESMF_SUCCESS) call ESMF_Finalize(endflag=ESMF_END_ABORT)
  
  ! Regridding using MOAB Mesh
  call profile_mesh_create(.true., file, rc=localrc)
   if (localrc /=ESMF_SUCCESS) then
     write(*,*) "ERROR IN REDIST SUBROUTINE!"
     call ESMF_Finalize(endflag=ESMF_END_ABORT)
    endif
  
  if (localPet .eq. 0) then
     write(*,*)
     write(*,*) "Success"
  endif

  ! Finalize ESMF
  call ESMF_Finalize(rc=localrc)
  if (localrc /=ESMF_SUCCESS) stop

  contains


 subroutine profile_mesh_create(moab, file, rc)
  logical, intent(in) :: moab
  character(*), intent(in) :: file
  integer, intent(out), optional :: rc

  integer :: localrc

  character(12) :: NM
  type(ESMF_VM) :: vm
  type(ESMF_Mesh) :: srcMesh

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

  NM = "NativeMesh"
  if (moab) then
    NM = "MBMesh"
  endif

#define profile_meshcreate
#ifdef profile_meshcreate
  call ESMF_TraceRegionEnter(trim(NM)//" ESMF_MeshCreate(DefaultDistribution)")
  call ESMF_VMLogMemInfo("before "//trim(NM)//" ESMF_MeshCreate(DefaultDistribution)")
#endif

  srcMesh=ESMF_MeshCreate(filename=file, fileformat=ESMF_FILEFORMAT_ESMFMESH, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#ifdef profile_meshcreate
  call ESMF_VMLogMemInfo("after "//trim(NM)//" ESMF_MeshCreate(DefaultDistribution)")
  call ESMF_TraceRegionExit(trim(NM)//" ESMF_MeshCreate(DefaultDistribution)")
#endif


  ! Free the meshes
  call ESMF_MeshDestroy(srcMesh, rc=localrc)
  if (localrc /=ESMF_SUCCESS) then
    rc=ESMF_FAILURE
    return
  endif

#endif
! ESMF_MOAB

end subroutine profile_mesh_create

end program MOAB_eval_create

