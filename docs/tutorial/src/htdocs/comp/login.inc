<:component /comp/logo.comp 
            uri=`CONNECTION.realUri`:>
<:default raiseOK `None`:>

<:if `not CONNECTION.hoptimeUser`:>
  <:args lusername password:>
  <:set submitted `CONNECTION.method=='POST'`:>
  <:if `submitted`:>
    <:import auth:>
    <:call `auth.getAuthorizer().login(CONNECTION, lusername, password)`:>
  <:/if:>
<:/if:>
<:if `not CONNECTION.hoptimeUser`:>
  <p><:component /comp/login_form.comp  
                 title=`submitted and "Login Incorrect" or "Login"`
                 action=`CONNECTION.realUri`
                 cache=yes:>
     <:url /register.html text="register":></p>
<:elif `raiseOK`:>
  <:import auth OK:>
  <:raise `OK`:>
<:else:>
  <p>You are logged in as
    <strong>
      <:component /comp/user.comp 
                user=`CONNECTION.hoptimeUser` 
                cache="yes":>
    </strong>.
    <:url /logout.html text="logout":></p>

<:/if:>


