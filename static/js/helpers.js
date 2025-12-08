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
export const validErrorData = (errorData) => {
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

export const loggedInNavbar = () => {

    const navBar = document.getElementById('navbarNav');

    const a1 = document.createElement('a');
    a1.className = 'nav-link';
    a1.href = '/todos-page';
    a1.textContent = 'Home';
    const li1 = document.createElement('li');
    li1.className = 'nav-item active';
    li1.appendChild(a1);
    const ul1 = document.createElement('ul');
    ul1.className = 'navbar-nav';
    ul1.appendChild(li1);

    const a2 = document.createElement('a');
    a2.className = 'btn btn-outline-light text-white';
    a2.type = 'button';
    a2.onclick = console.log;
    a2.textContent = 'Logout';
    const li2 = document.createElement('li');
    li2.className = 'nav-item m-1';
    li2.appendChild(a2);
    const ul2 = document.createElement('ul');
    ul2.className = 'navbar-nav ml-auto';
    ul2.appendChild(li2);

    navBar.appendChild(ul1);
    navBar.appendChild(ul2);
}