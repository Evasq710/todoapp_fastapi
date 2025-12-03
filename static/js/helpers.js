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