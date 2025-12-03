/*
* CREATE A NEW USER
* */
const registerForm = document.getElementById('registerForm');
if(registerForm){
    /*
    * 'SUBMIT' Event Listener
    * */
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const form = e.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        if (data.password !== data.verification) {
            alert("Passwords do not match");
            return;
        }

        const payload = {
            username: data.username,
            email: data.email,
            phone_number: data.phone_number,
            first_name: data.firstname,
            last_name: data.lastname,
            password: data.password
        };

        try {
            const response = await fetch('/auth/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (response.ok){
                // Redirecting to the LOGIN page
                alert("Successful registration");
                window.location.href = '/login-page';
            } else {
                const errorData = await response.json();
                if (!validErrorData(errorData)){
                    console.log(errorData);
                    alert('An error occurred while trying to register the user. Try again later.')
                    return;
                }

                if (typeof errorData.detail === 'string'){
                    alert(`Error: ${errorData.detail}`);
                } else {
                    alert(`Error on ${errorData.detail[0].loc[1]}: ${errorData.detail[0].msg}`);
                }
            }
        } catch (error){
            console.log(`Error: ${error}`);
            alert('An error occurred. Please try again.')
        }
    })
}


/*
* Validating Error Schema:
 {
  "detail": [
    {
      "loc": [ "string", 0 ],
      "msg": "string",
      "type": "string"
    }
  ]
}
* */
const validErrorData = (errorData) => {
    if (typeof errorData !== 'object') return false;
    if (!('detail' in errorData)) return false;
    if (typeof errorData.detail !== 'string' && !Array.isArray(errorData.detail)) return false;
    if (Array.isArray(errorData.detail)){
        if (errorData.detail.length === 0) return false;
        errorData.detail.forEach(error => {
            if (typeof error !== 'object') return false;
            if (!('msg' in error)) return false;
            if (!('loc' in error)) return false;
            if (!Array.isArray(error.loc)) return false;
            if(error.loc.length !== 2) return false;
        });
    }
    return true;
}