import { validErrorData } from './helpers.js';

/*
 - Access token in the Authorization Header (stored in the browser's memory)
 - Refresh token in an HTTP-only cookie
 */

/*
* LOGIN
* */
const loginForm = document.getElementById('loginForm');
if(loginForm) {
    /*
    * 'SUBMIT' Event Listener
    * */
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault()

        /*
        * FastAPI expects username and password inside a OAuth2PasswordRequestForm object
        * We can send data in this format by sending the credentials as form data, NOT as JSON.
        * There are two ways to do this:
        * 1. Send a FormData object to the body.
        *    The Content-Type header (that is going to be handled automatically by fetch) will be:
        *     - multipart/form-data;
        *           Used when submitting HTML forms containing files or a combination of various data
        *     - boundary=----WebKitFormBoundary<random_string>
        *           The random string acts as a unique delimiter that marks the beginning and end of each
        *           individual part within the multipart/form-data request body
        * 2. Send the expected key-values using URLSearchParams.
        *     - Content-Type header: application/x-www-form-urlencoded:
        *           This has to be manually set (the Fetch API does not automatically infer it when the body is a simple string.)
        *     - body: urlSearchParamsObject.toString()
        *           The parameters will have the following structure: username=<username>&password=<password>
        *     - Additional code, in order to create the URLSearchParams object:
                    const payload = new URLSearchParams();
                    formData.entries().forEach(([key, value]) => payload.append(key, value));
                    * ...body: payload.toString()
        * */

        const form = e.target;
        const formData = new FormData(form);

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                body: formData
            });

            const responseData = await response.json();

            if (response.ok && 'access_token' in responseData) {
                // FIXME! This is not the best solution to store the access token. Consider using Redux
                window.sessionStorage.setItem('access_token', responseData.access_token);
                // Redirecting to the TODOs page
                window.location.href = '/todos-page';
            } else if (response.ok){
                console.log(responseData);
                alert('An error occurred. Please try again later.')
            } else {
                if (!validErrorData(responseData)){
                    console.log(responseData);
                    alert('An error occurred while trying to log in. Try again later.')
                    return;
                }

                if (typeof responseData.detail === 'string'){
                    alert(`Error: ${responseData.detail}`);
                } else {
                    alert(`Error on ${responseData.detail[0].loc[1]}: ${responseData.detail[0].msg}`);
                }
            }
        } catch (error){
            console.log(`Error: ${error}`);
            alert('An error occurred. Please try again.')
        }
    })
}