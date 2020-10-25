const { Router } = require('express');
const router = Router();


const User = require('../models/user');
const jwt = require('jsonwebtoken');

router.get('/', (req, res) => {
res.send('Hello word')
});

router.post('/signUp', async (req, res) => {
    const { email, password } = req.body;
    const newUser = new User({ email, password });
    await newUser.save();

    const token = jwt.sign({ _id: newUser._id }, 'secretKey')

    res.status(200).json({ token })

})




router.post('/signIn', async (req, res) => {
    const { email, password } = req.body;
    const user = await User.findOne({ email })

    if (!user) return res.status(401).send('the email doesn;t exists');
    if (user.password !== password) return res.status(401).send('wrong password');

    const token = jwt.sign({ _id: user._id }, 'secretKey');
    return res.status(200).json({ token });

});


//mas rutas

//applicaciones//////////////////////////////////////

router.get('/app', (req, res) => {
    res.json([
        {
            _id: 1,
            name: 'App',
            description: 'lorem',
            date: "2020-10-22T23:31:04.542Z"
        }
    ])
})


router.get('/private-app', verifyToken, (req, res) => {
    res.json([
        {
            _id: 1,
            name: 'App',
            description: 'lorem',
            date: "2020-10-22T23:31:04.542Z"
        }
    ])

})


router.get('/users',verifyToken,(req,res)=>{
    res.send(req.userId);

})



module.exports = router;


function verifyToken(req, res, next) {


    if (!req.headers.authorization) {
        return res.status(401).send('Authorize request');
    }

    const token= req.headers.authorization.split(' ')[1]
    if(token=='null'){
        return res.status(401).send('unauthorize request');
    }


    const payload=jwt.verify(token,'secretKey');
    req.userId=payload._id;
    
    
    next();

    
module.exports = router;
    

}



