M.AutoInit();

console.log(document.cookie);

function get_cookie(key) {
	cookies = document.cookie.split('; ');

	for (let i = 0; i < cookies.length; i++) {
		c = cookies[i].split('=');
		if (c[0] == key) return c[1];
	}
}
