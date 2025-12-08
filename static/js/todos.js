
window.addEventListener('DOMContentLoaded', async (e) => {
    try {
        let response = await getUserTodos();
        let responseData = await response.json();

        if(response.status === 401){
            // Trying to get a new access token
            const newTokenSuccessful = await getNewAccessToken();

            if(!newTokenSuccessful){
                // Refresh token is not valid. Redirecting to login page
                window.sessionStorage.removeItem('access_token');
                window.location.href = '/login-page';
                return;
            }

            // Refresh token is valid, so we updated the access token successfully
            // Trying to get user's todos again
            response = await getUserTodos();
            responseData = await response.json();
        }

        if (response.ok){
            // Valid access Token (either and old token or a new one). We were able to get user's todos
            createTodosTable(responseData);
            return;
        }

        // Something went wrong with the GET Todos request
        if('detail' in responseData) {
            alert(responseData.detail)
        } else {
            alert('An error occurred while trying to get todos. Please try again.');
        }
    } catch (error){
        console.log(`Error: ${error}`);
        alert('An unexpected error occurred while trying to get todos. Please try again.');
    }
});


/*
* HELPERS
* */

const getUserTodos = async () => {
    return await fetch('/todo/', {
        method: 'GET',
        headers: {
            // FIXME! sessionStorage is not the best solution
            'Authorization': `Bearer ${window.sessionStorage.getItem('access_token')}`
        }
    });
}

const getNewAccessToken = async () => {
    const refreshResponse = await fetch('auth/refresh');
    const refreshData = await refreshResponse.json();
    if (refreshResponse.ok && 'access_token' in refreshData) {
        window.sessionStorage.setItem('access_token', refreshData.access_token)
        return true;
    }
    return false;
}

const createTodosTable = (todos) => {
    const tBody = document.getElementById('table');

    todos.forEach((todo, index) => {
        const row = document.createElement('tr');
        const td1 = document.createElement('td');
        const td2 = document.createElement('td');
        const td3 = document.createElement('td');
        const editBtn = document.createElement('button');

        td1.textContent = index;
        td2.textContent = todo.title;
        editBtn.textContent = 'Edit';
        editBtn.className = 'btn btn-info';
        td3.appendChild(editBtn);

        if(todo.completed){
            row.className = 'pointer alert alert-success';
            td2.className = 'strike-through-td';
        } else {
            row.className = 'pointer';
        }

        row.appendChild(td1);
        row.appendChild(td2);
        row.appendChild(td3);
        tBody.appendChild(row);
    })
}