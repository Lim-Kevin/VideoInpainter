function again() {
    fetch('again', {
        method: 'POST'
    }).then((response)=>{
        if(response.redirected){
            window.location.href = response.url;
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}