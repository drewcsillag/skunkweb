<:if `not CONNECTION.hoptimeUser`:>
  <:args username password:>
  <:set submitted `CONNECTION.method=='POST'`:>
  <:if `submitted`:>
    <:import auth:>
    <:call `auth.getAuthorizer().login(CONNECTION, username, password)`:>
  <:/if:>
<:/if:>
<:if `not CONNECTION.hoptimeUser`:>
  <p><:component /comp/login_form.comp  
                 title=`submitted and "Login Incorrect" or "Login"`
                 cache=yes:></p>
<:else:>
  <p>You are logged in as
    <strong><:component /comp/user.comp 
                user=`CONNECTION.hoptimeUser` 
                cache="yes":></strong>.</p>
  <p><:url logout.html text="Logout":></p>
<:/if:>


