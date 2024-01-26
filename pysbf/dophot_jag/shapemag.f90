! Function shapemag(starpar,npstar)
!
! This function takes the appropiate star parameters and 
! determine a magnitude in precisely the same way that DOTODAO does it.

function shapemag(starpar,npstar)

  IMPLICIT REAL(8) (A-H,O-Z)
  real(8) :: starpar(npstar)

  amag = starpar(2)*ELLIPAREA(starpar(5),starpar(6),starpar(7))
  if(amag.le.0.0) then
     amag = 99.999
     return
  end if
  shapemag = -2.5*dlog10(amag)+23.5
  
end function shapemag