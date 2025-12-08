
/*
* CREATE A NEW TODO
* */

const todoForm = document.getElementById('todoForm');
if (todoForm) {
    /*
    * 'SUBMIT' Event Listener
    * */
    todoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        const payload = {
            title: data.title,
            description: data.description,
            priority: parseInt(data.priority),
            completed: false
        };
        
        try {
            // Will throw an exception if the cookie is not found
            const accessToken = getCookie('access_token', 'Authentication token not found');
            
            const response = await fetch('/todo/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok){
                form.reset(); // Clearing the form
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail}`);
            }
        } catch (error){
            console.log(`Error: ${error}`);
            alert('An error occurred. Please try again.')
        }
    });
}

/*
* EDIT TODO
* */
const editTodoForm = document.getElementById('editTodoForm');
if(editTodoForm){
    /*
    * 'SUBMIT' Event Listener
    * */
    editTodoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        var url = window.location.pathname;
        const todoId = url.substring(url.lastIndexOf('/') + 1);
        
        const payload = {
            title: data.title,
            description: data.description,
            priority: parseInt(data.priority),
            completed: data.complete === "on"
        };
        
        try {
            // Will throw an exception if the cookie is not found
            const accessToken = getCookie('access_token', 'Authentication token not found');
            
            const response = await fetch(`/todo/${todoId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok){
                // Redirecting to the TODO page
                window.location.href = '/todos/todo-page';
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.detail}`);
            }
        } catch (error){
            console.log(`Error: ${error}`);
            alert('An error occurred. Please try again.')
        }
    })
}

/*
* DELETE TODO
* */
const deleteTodoButton = document.getElementById('deleteButton');
if (deleteTodoButton) {
    /*
    * 'CLICK' Event Listener
    * */
    deleteTodoButton.addEventListener('click', async () => {
        var url = window.location.pathname;
        const todoId = url.substring(url.lastIndexOf('/') + 1);

        console.log("FIXME: Delete TODO logic")
    })
}


/*
* HELPERS
* */
const getCookie = (cookieName, errorMessage = 'Cookie not found') => {
    const cookie = 'FIXME: tempCookie';
    
    if(!cookie) {
        throw new Error(errorMessage);
    }
    return cookie;
}


/* LOGOUT */

const logout = async () => {
    try{
        const response = await fetch('/auth/refresh', {
            method: 'DELETE'
        });
        // TODO: Delete access_token from sessionStorage
        const responseData = await response.json();
        console.log(responseData);
    } catch (error){
        console.error(`Couldn't call logout endpoint. Error: ${error}`)
    }
}

// TODO: DELETE access_token from sessionStorage
