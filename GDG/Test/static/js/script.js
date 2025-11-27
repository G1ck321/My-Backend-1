  const myForm = document.getElementById('userForm');
        const myName = document.getElementById('name');
        const myEmail = document.getElementById('email');
        const communityCheckbox = document.getElementById('community');
        const telegramSection = document.getElementById('telegramSection');
        const btnText = document.getElementById('btnText');
        const loader = document.getElementById('loader');
        const successMsg = document.getElementById('successMsg');

        // Show/hide Telegram link based on checkbox state
        // communityCheckbox.addEventListener('change', function() {
        //     if (this.checked) {
        //         telegramSection.classList.add('hidden');
        //     } else {
        //         telegramSection.classList.remove('hidden');
        //     }
        // });

        myForm.addEventListener("submit", (e) => {
            e.preventDefault();

            // Check if not in community - redirect to Telegram
            // if (!communityCheckbox.checked) {
            //     window.open('https://t.me/styluscommunity', '_blank');
            //     return;
            // }

            let data = {
                name: myName.value,
                email: myEmail.value,
                inCommunity: true
            };

            // Show loading
            btnText.style.display = 'none';
            loader.classList.remove('hidden');

            async function postData() {
                const options = {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                };
                const response = await fetch("/api/create", options);
                const details = await response.json();
                console.log(details);
                
                // Success
                loader.classList.add('hidden');
                btnText.style.display = 'inline';
                btnText.textContent = 'Joined Successfully!';
                successMsg.textContent = "🎉 You're on the list! We'll be in touch.";
                successMsg.classList.remove('hidden');
                e.target.reset();
                myName.value=""
                myEmail.value = ""
            }
            postData();
        });