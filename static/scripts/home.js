if (get_cookie('loggedin') != 'true') {
	window.location = 'auth';
}

id = '';

function getWalletAmount() {
	fetch('/getwalletamount', {
		method: 'GET',
		headers: {
			username: get_cookie('username'),
			password: get_cookie('password'),
		},
	})
		.then((response) => response.json())
		.then((data) => {
			document.getElementById('balance-amount').innerText = 'Rs. ' + data.wallet_amount;
		});
}

function getPendingApproval() {
	fetch('/getpendingapproval', {
		method: 'GET',
		headers: {
			username: get_cookie('username'),
			password: get_cookie('password'),
		},
	})
		.then((response) => response.json())
		.then((data) => {
			console.log(data);
			if (data.status == 'success' && data.payment_amount != undefined) {
				document.getElementById('approval-location').innerText = data.location;
				document.getElementById('approval-amount').innerText = 'Rs. ' + data.payment_amount;
				document.getElementById('approval').style.display = 'block';
				id = data.id;
			}
		});
}

function addToWallet() {
	let amount = document.getElementById('amount').value;
	if (amount.length <= 0) return;

	fetch('/addtowallet', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			username: get_cookie('username'),
			password: get_cookie('password'),
		},
		body: JSON.stringify({
			additional_wallet_amount: document.getElementById('amount').value,
		}),
	})
		.then((response) => response.json())
		.then((data) => {
			document.getElementById('balance-amount').innerText = 'Rs. ' + data.wallet_amount;
			document.getElementById('amount').value = '';
		})
		.catch((err) => console.log(err));
}

function approve() {
	fetch('/approve', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			username: get_cookie('username'),
			password: get_cookie('password'),
		},
		body: JSON.stringify({
			id: id,
		}),
	})
		.then((response) => response.json())
		.then((data) => {
			console.log(data);
			document.getElementById('approval').style.display = 'none';
            document.getElementById('balance-amount').innerText = 'Rs. ' + data.wallet_amount;
		});
}

function logout() {
	document.cookie = 'username=;';
	document.cookie = 'password=;';
	document.cookie = 'loggedin=false;';
	window.location = 'auth';
}

getWalletAmount();
getPendingApproval();
