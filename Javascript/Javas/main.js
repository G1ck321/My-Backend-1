let xp = 0;
let health = 100;
let gold = 50;
let currentWeapon = 0;
//let is best used over var
let inventory = ["stick"];
let monsterHealth, fighting;//initialize

const button1 = document.querySelector("#button1");
const button2 = document.querySelector("#button2");
const button3 = document.querySelector("#button3");
const text = document.querySelector("#text");
const xpText = document.querySelector("#xpText");
const healthText = document.querySelector("#healthText");
const goldText = document.querySelector("#goldText");
const monsterStats = document.querySelector("#monsterStats");
const monsterNameText = document.querySelector("#monsterName");
const monsterHealthText = document.querySelector("#monsterHealth");
//
const weapon = [
    {
        name: "stick",
        power: 5
    },
    {
        name: "dagger",
        power: 30
    },
    {
        name: "claw hammer",
        power: 50
    },
    {
        name: "sword",
        power: 100
    }];
//
const monsters = [{
    name: "fanged beast",
    level: 8,
    health: 60
},
{
    name: "slime",
    level: 2,
    health: 15
},

{
    name: "dragon",
    level: 20,
    health: 300
}
];
const locations = [
    {
        name: "town square",
        "button-text": ["Go to store",
            "Go to cave",
            "Fight dragon"],
        "button-functions": [goStore, goCave, fightDragon],
        text: "You are in Town Square. You see a sign that says \'store'"
    },
    {
        name: "store",
        "button-text": ["Buy 10 health (10 gold)",
            "Buy weapon(30 gold)",
            "Go to town square"],
        "button-functions": [buyHealth, buyWeapon, goTown],
        text: "You are in Town Square. You see a sign that says \'store' "
    },
    {
        name: "cave",
        "button-text": ["Fight fanged Beast",
            "Fight Slime",
            "Go to town square"],
        "button-functions": [fightBeast, fightSlime, goTown],
        text: "You are in Town Square. You see a sign that says \'store' "
    },
    {
        name: "fight",
        "button-text": ["Attack", "Dodge", "Run"],
        "button-functions": [attack, dodge, goTown],
        text: "You are fighting a monster. "
    },
    {
        name: "kill monster",
        "button-text": ["Go to town square", "Go to town square", "Go to town square"],
        "button-functions": [goTown, goTown, easterEgg],
        text: "congratulations 🎉.The monster dies. You gain experience points and find gold.   "
    },
    {
        name: "lose",
        "button-text": ["REPLAY?", "REPLAY?", "REPLAY?"],
        "button-functions": [restart, restart, restart],
        text: "You lose 😢"
    },
    {
        name: "win",
        "button-text": ["REPLAY?", "REPLAY?", "REPLAY?"],
        "button-functions": [restart, restart, restart],
        text: "You have defeated the dragon , you win🎉"
    },
    {
        name: "easter egg",
        "button-text": ["2", "8", "Go to town square"],
        "button-functions": [PickTwo, PickEight, goTown],
        text: "You find a secret Gamepad, pick a game number above. \
        Ten numbers will be chosen randomly between numbers 0 and 10. \
        If the number you chose matches one of the random numbers, you win!"
    }
];
//when your key does not have "" you can use . notation
//{} is an object it contains value pairs name is the property name
// button-text needs "" because of hyphen '-'

//button1.onclick = goStore;
// button2.onclick = goCave;
//do not do goStore() it calls it
button1.onclick = goStore;
button2.onclick = goCave;
button3.onclick = fightDragon;
//onclick can only store one function at a time 
//so if you assign to call two functions one after another the second will override first and run alone
//addEventlistener is better

function update(location) {
    monsterStats.style.display = "none";
    button1.innerText = location["button-text"][0];
    button2.innerText = location["button-text"][1];
    button3.innerText = location["button-text"][2];
    button1.onclick = location["button-functions"][0];
    button2.onclick = location["button-functions"][1];
    button3.onclick = location["button-functions"][2];
    text.innerText = location.text;
}

//
function goTown() {
    update(locations[0]);
}
//
function goStore() {
    update(locations[1]);
}
//
function goCave() {
    update(locations[2])
}
//
function buyHealth() {
    if (gold >= 10) {
        gold -= 10;
        health += 10;
        goldText.innerText = gold;
        healthText.innerText = health;
    }
    else {
        text.innerText = "You did not have enough cash to buy gold. ";
    }
}
function buyWeapon() {
    if (currentWeapon < weapon.length - 1) {
        if (gold >= 30) {
            gold -= 30;
            goldText.innerText = gold
            currentWeapon++;
            let newWeapon = weapon[currentWeapon].name
            text.innerText = "You now have a " + newWeapon + ".\n";
            inventory.push(newWeapon);
            text.innerText += "In your inventory you have: " + inventory;
        }
        else {
            text.innerText = "You do not have enough gold to buy a weapon.";
        }
    } else {
        text.innerText = "You already have the most powerful weapon!";
        button2.innerText = "Sell weapon for 15 gold";
        button2.onclick = sellWeapon;
    }
}
//
function sellWeapon() {
    if (inventory.length > 1) {
        gold += 15;
        goldText.innerText = gold;
        let currentWeapon = inventory.shift();//removes first element
        //this let is only used within this function scope.
        text.innerText = "You sold a " + currentWeapon + " . ";
        text.innerText += "In your inventory you have: " + inventory;
    }
    else {
        text.innerText = "Don't sell all weapons. ";
    }
}
//
function fightBeast() {
    fighting = 0;
    goFight();
}
//
function fightSlime() {
    fighting = 1;
    goFight();
}
//
function fightDragon() {
    fighting = 2;
    goFight();
}
//
function goFight() {
    update(locations[3]);
    monsterHealth = monsters[fighting].health;
    monsterStats.style.display = "block";
    monsterNameText.innerText = monsters[fighting].name;
    monsterHealthText.innerText = monsterHealth;
}
//
function attack() {
    text.innerText = "The " + monsters[fighting].name + " attaks.";
    text.innerText += "You attack it with your " + weapon[currentWeapon].name + ".";
    if (monsterHit()) {
        // console.log(monsterHit());
        health -= getMonsterAtkValue(monsters[fighting].level);
        monsterHealth -= weapon[currentWeapon].power + Math.floor(Math.random() * xp) + 1;
    }
    else {
        text.innerText += " You miss and take some damage."
        health -=weapon[currentWeapon].power-Math.floor((Math.random()*xp)+(Math.random()*monsters[fighting].level))
        console.log(monsterHealth+'Y')
    }


    console.log(monsterHealth)
    healthText.innerText = health;
    monsterHealthText.innerText = monsterHealth
    if (health <= 0) {
        lose();
    }
    else if (monsterHealth <= 0) {
        fighting === 2 ? WinGame() : defeatMonster();
        //     if (fighting === 2) {
        //         WinGame();
        //     }
        //     else{
        //     defeatMonster();
        // }
    }
    //
    if (Math.random() <= .1 && inventory.length !== 1) {

        text.innerText = "Your " + inventory.pop() + " breaks. ";
        currentWeapon--;
    }
}

function getMonsterAtkValue(level) {
    let hit = (level * 5) - (Math.floor(Math.random() * xp));
    console.log(hit);
    return hit;
}
//beast is 0 slime is 1 dragon is 2
function monsterHit() {
    if (fighting == 0) {
        return Math.random() > .3 || health <= 25; //true or false
    }
    else if (fighting == 1) {
        return Math.random() > .2 || health <= 20; //true or false
    }
    else {
        return Math.random() > .5 || health <= 30; //true or false
    }
}
//
function dodge() {
    text.innerText = "You dodged an attack from the " + monsters[fighting].name + ".";
}
//
function defeatMonster() {
    gold += Math.floor(monsters[fighting].level * 6.7);
    xp += monsters[fighting].level;
    goldText.innerText = gold;
    xpText.innerText = xp;
    update(locations[4]);
}
//
function lose() {
    update(locations[5]);
}
function WinGame() {
    update(locations[6]);
}
function restart() {
    xp = 0;
    health = 100;
    gold = 50;
    currentWeapon = 0;
    inventory = ["stick"];
    goldText.innerText = gold;
    healthText.innerText = health;
    xpText.innerText = xp;
    goTown();
}
//You can not assign as let then assign as const in same scope unless in function
function easterEgg() {
    update(locations[7]);
}
function PickTwo() {
    pick(2);
}
function PickEight() {
    pick(8);
}
function pick(guess) {
    let numbers = [];
    while (numbers.length < 10) {
        numbers.push(Math.floor(Math.random() * 11))//the random module only gives within 0 and 0.99
    }
    text.innerText = "You picked " + guess + ", Here are the random numbers:\n";
    //you initialize the variable, then condition
    for (let i = 0; i < 10; i++) {
        text.innerText += numbers[i] + "\n";
        console.log(numbers[i])
    }
    //we're looking for the index of a number, 
    //returns an number or -1 if not there.
    if (numbers.indexOf(guess) !== -1) {
        text.innerText += "Right! You win 20 gold!";
        gold +=20;
        goldText.innerText = gold;
    }
    else{
        text.innerText += "Wrong! You lose 10 health!";
        health -=10;
        healthText.innerText = health;
    }
    if (health<=10){
        lose();
    }
}
